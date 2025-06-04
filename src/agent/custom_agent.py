import json
import traceback
import logging
import asyncio
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Set,
    Deque,
    Union,
)
import os
import asyncio
import time
from enum import Enum, nonmember
from pydantic import BaseModel, ValidationError
from collections import deque, defaultdict
from browser_use.agent.prompts import SystemPrompt, AgentMessagePrompt
from browser_use.agent.service import Agent
from browser_use.agent.views import (
    ActionResult,
    AgentHistoryList,
    AgentOutput,
    AgentState,
    StepMetadata,
    ToolCallingMethod,
)
from browser_use.agent.gif import create_history_gif
from browser_use.browser.browser import Browser
from browser_use.browser.profile import BrowserProfile
from browser_use.browser.session import BrowserSession
from browser_use.browser.context import BrowserContext
from browser_use.controller.service import Controller
from browser_use.controller.registry.views import ActionModel
from browser_use.utils import time_execution_async
from browser_use.agent.views import AgentError
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from playwright.sync_api import Request, Response

from json_repair import repair_json
from src.utils.agent_state import AgentState
from src.agent.client import AgentClient
from src.utils import retry_async, RetryError

from eval.ctf_server.client import EvalClient

from johnllm import LLMModel, LMP
from httplib import HTTPRequest, HTTPResponse, HTTPMessage

from logging import getLogger
from logger import init_root_logger

# from .state import CustomAgentOutput
from common.agent import BrowserActions
from .custom_views import CustomAgentOutput
from .custom_message_manager import CustomMessageManager, CustomMessageManagerSettings
from .custom_views import CustomAgentStepInfo, CustomAgentState
from .http_handler import HTTPHistory, HTTPHandler
from .logger import AgentLogger
from .discovery import update_plan, generate_plan, PLANNING_TASK_TEMPLATE

logger = getLogger(__name__)

Context = TypeVar("Context")

DEFAULT_INCLUDE_MIME = ["html", "script", "xml", "flash", "other_text"]
DEFAULT_INCLUDE_STATUS = ["2xx", "3xx", "4xx", "5xx"]
MAX_PAYLOAD_SIZE = 4000
DEFAULT_FLUSH_TIMEOUT = 5.0  # seconds to wait for all requests to be flushed
DEFAULT_PER_REQUEST_TIMEOUT = 2.0  # seconds to wait for *each* unmatched request
DEFAULT_SETTLE_TIMEOUT = 1.0  # seconds of network "silence" after the *last* response
POLL_INTERVAL = 0.5  # how often we poll internal state


class AgentObservations(str, Enum):
    SITE_STRUCTURE = "site_structure"


class NewPage(BaseModel):
    is_new_page: bool


class IsNewPage(LMP):
    prompt = """
You are tasked with determining if the current DOM state of a browser is the same or different page from the previous one,
indicating that the browser has executed a navigational action between the two states. Be careful to differentiate between
different webpages and the same webpage with a slightly changed view (ie. popup, menu dropdown, etc.)

Here is the new page:
{{new_page}}

Here is the previous page:
{{old_page}}

You are tasked with determining if the current DOM state of a browser is the same or different page from the previous one,
indicating that the browser has executed a navigational action between the two states. Be careful to differentiate between
different webpages and the same webpage with a slightly changed view (ie. popup, menu dropdown, etc.)

Now answer, has the page changed?
"""
    response_format = NewPage


# REFACTORED CHANGES:
# - not using customg agent output and falling back to default defined in Agent
# - removed state update w.e this does
# - need add error-handling in step()


# Planning Agent:
# - need to detect when page has changed to
class CustomAgent(Agent):
    def __init__(
        self,
        task: str,
        llm: BaseChatModel,
        model_name: str = "command-a-03-2025",
        add_infos: str = "",
        http_handler: HTTPHandler = None,
        # Optional parameters
        browser: Browser | None = None,
        browser_context: BrowserContext | None = None,
        browser_profile: BrowserProfile | None = None,
        browser_session: BrowserSession | None = None,
        controller: Controller[Context] = Controller(),
        # Initial agent run parameters
        sensitive_data: Optional[Dict[str, str]] = None,
        initial_actions: Optional[List[Dict[str, Dict[str, Any]]]] = None,
        # Cloud Callbacks
        register_new_step_callback: (
            Callable[["BrowserState", "AgentOutput", int], Awaitable[None]] | None
        ) = None,
        register_done_callback: (
            Callable[["AgentHistoryList"], Awaitable[None]] | None
        ) = None,
        register_external_agent_status_raise_error_callback: (
            Callable[[], Awaitable[bool]] | None
        ) = None,
        # Agent settings
        use_vision: bool = True,
        use_vision_for_planner: bool = False,
        save_conversation_path: Optional[str] = None,
        save_conversation_path_encoding: Optional[str] = "utf-8",
        max_failures: int = 3,
        retry_delay: int = 10,
        system_prompt_class: Type[SystemPrompt] = SystemPrompt,
        agent_prompt_class: Type[AgentMessagePrompt] = AgentMessagePrompt,
        max_input_tokens: int = 128000,
        validate_output: bool = False,
        message_context: Optional[str] = None,
        generate_gif: bool | str = False,
        available_file_paths: Optional[list[str]] = None,
        include_attributes: list[str] = [
            "title",
            "type",
            "name",
            "role",
            "aria-label",
            "placeholder",
            "value",
            "alt",
            "aria-expanded",
            "data-date-format",
        ],
        max_actions_per_step: int = 10,
        tool_calling_method: Optional[ToolCallingMethod] = "auto",
        page_extraction_llm: Optional[BaseChatModel] = None,
        planner_llm: Optional[BaseChatModel] = None,
        planner_interval: int = 1,  # Run planner every N steps
        # Inject state
        injected_agent_state: Optional[AgentState] = None,
        context: Context | None = None,
        history_file: Optional[str] = None,
        agent_client: Optional[AgentClient] = None,
        eval_client: Optional[EvalClient] = None,
        app_id: Optional[str] = None,
        close_browser: bool = False,
        agent_name: str = "",
    ):
        if not http_handler:
            raise Exception("Must initialize CustomAgent with HTTPHandler")

        super(CustomAgent, self).__init__(
            task=task,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            browser_session=browser_session,
            controller=controller,
            sensitive_data=sensitive_data,
            initial_actions=initial_actions,
            register_new_step_callback=register_new_step_callback,
            register_done_callback=register_done_callback,
            register_external_agent_status_raise_error_callback=register_external_agent_status_raise_error_callback,
            use_vision=use_vision,
            use_vision_for_planner=use_vision_for_planner,
            save_conversation_path=save_conversation_path,
            save_conversation_path_encoding=save_conversation_path_encoding,
            max_failures=max_failures,
            retry_delay=retry_delay,
            # system_prompt_class=system_prompt_class,
            max_input_tokens=max_input_tokens,
            validate_output=validate_output,
            message_context=message_context,
            generate_gif=generate_gif,
            available_file_paths=available_file_paths,
            include_attributes=include_attributes,
            max_actions_per_step=max_actions_per_step,
            tool_calling_method=tool_calling_method,
            page_extraction_llm=page_extraction_llm,
            planner_llm=planner_llm,
            planner_interval=planner_interval,
            injected_agent_state=None,
            context=context,
        )
        self.http_handler = http_handler
        self.model_name = model_name
        self.agent_name = agent_name
        self.close_browser = close_browser
        self.curr_page = None
        self.history_file = history_file
        self.http_history = HTTPHistory()
        self.agent_client = agent_client
        self.eval_client = eval_client
        if self.eval_client:
            self.eval_client.set_shutdown(self.shutdown)

        self.app_id = app_id
        self.agent_id = None
        if agent_client and not app_id:
            raise ValueError("app_id must be provided when agent_client is set")

        # username = self.agent_client.username if self.agent_client else "default"
        username = self.agent_name if self.agent_name else "default"
        init_root_logger(username)
        self.observations = {title.value: "" for title in AgentObservations}

        self.state = CustomAgentState()
        self.add_infos = add_infos
        self._message_manager = CustomMessageManager(
            task=task,
            system_message=SystemPrompt(
                action_description=self.unfiltered_actions,
                max_actions_per_step=self.settings.max_actions_per_step,
                # override_system_message=override_system_message,
                # extend_system_message=extend_system_message,
            ).get_system_message(),
            settings=CustomMessageManagerSettings(
                max_input_tokens=self.settings.max_input_tokens,
                include_attributes=self.settings.include_attributes,
                message_context=self.settings.message_context,
                sensitive_data=sensitive_data,
                available_file_paths=self.settings.available_file_paths,
                agent_prompt_class=agent_prompt_class,
            ),
            state=self.state.message_manager_state,
        )

        # State variables used for step()
        self.step_http_msgs = []

    def handle_page(self, page):
        logger.info(f"[PLAYWRIGHT] >>>>>>>>>>>")
        logger.info(f"[PLAYWRIGHT] Frame {page}")
        self.curr_page = page

    def _is_new_page(self, old_page: str, new_page: str) -> bool:
        """Check if the new page is different from the old page"""
        try:
            is_new_page = IsNewPage().invoke(
                model=self.llm,
                model_name=self.model_name,
                prompt_args={
                    "new_page": new_page,
                    "old_page": old_page,
                },
            )
            return is_new_page.is_new_page
        except Exception as e:
            logger.error(f"Error in _is_new_page: {e}")
            return False

    def _log_response(
        self,
        http_msgs: List[HTTPMessage],
        current_msg: BaseMessage,
        response: CustomAgentOutput,
    ) -> None:
        """Log the model's response"""
        if "Success" in response.current_state.evaluation_previous_goal:
            emoji = "✅"
        elif "Failed" in response.current_state.evaluation_previous_goal:
            emoji = "❌"
        else:
            emoji = "🤷"

        logger.info(f"{emoji} Eval: {response.current_state.evaluation_previous_goal}")
        # logger.info(f"🧠 New Memory: {response.current_state.important_contents}")
        # logger.info(f"🤔 Thought: {response.current_state.thought}")
        logger.info(f"🎯 Next Goal: {response.current_state.next_goal}")
        for i, action in enumerate(response.action):
            logger.info(
                f"🛠️  Action {i + 1}/{len(response.action)}: {action.model_dump_json(exclude_unset=True)}"
            )
        logger.info(f"[Prev Messages]: {current_msg.content}")
        logger.info(f"Captured {len(http_msgs)} HTTP Messages")
        for msg in http_msgs:
            logger.info(f"[Agent] {msg.request.url}")

    # def _setup_action_models(self) -> None:
    #     """Setup dynamic action models from controller's registry"""
    #     # Get the dynamic action model from controller's registry
    #     self.ActionModel = self.controller.registry.create_action_model()
    #     # Create output model with    the dynamic actions
    #     self.AgentOutput = CustomAgentOutput.type_with_custom_actions(self.ActionModel)

    def update_step_info(
        self,
        model_output: CustomAgentOutput,
        step_info: Optional[CustomAgentStepInfo] = None,
    ):
        """
        update step info
        """
        if step_info is None:
            return

        step_info.step_number += 1
        # important_contents = model_output.current_state.important_contents
        # if (
        #         important_contents
        #         and "None" not in important_contents
        #         and important_contents not in step_info.memory
        # ):
        #     step_info.memory += important_contents + "\n"

        logger.info(f"🧠 All Memory: \n{step_info.memory}")

    @time_execution_async("--get_next_action")
    async def get_next_action(
        self, input_messages: List[BaseMessage]
    ) -> CustomAgentOutput:
        """Get next action from LLM based on current state"""
        ai_message = self.llm.invoke(
            input_messages,
            # model_name=self.model_name,
            # response_format=None
        )
        # for tracking message history
        self._message_manager._add_message_with_tokens(ai_message)
        ai_content = ai_message.content.replace("```json", "").replace("```", "")
        ai_content = repair_json(ai_content)
        parsed_json = json.loads(ai_content)
        logger.info(f"[PARSED]: ", parsed_json)

        parsed: AgentOutput = self.AgentOutput(**parsed_json)

        if parsed is None:
            logger.debug(ai_message.content)
            raise ValueError("Could not parse response.")

        # cut the number of actions to max_actions_per_step if needed
        if len(parsed.action) > self.settings.max_actions_per_step:
            parsed.action = parsed.action[: self.settings.max_actions_per_step]
        return parsed

    async def execute_ancillary_actions(self, input_messages: List[BaseMessage]):
        pass

    async def _update_server(
        self, http_msgs: List[HTTPMessage], browser_actions: BrowserActions
    ) -> None:
        """Executed after the agent takes action and browser state is updated"""
        if self.agent_client:
            if not self.agent_id:
                agent_info = await self.agent_client.register_agent(self.app_id)
                self.agent_id = agent_info["id"]

            await self.agent_client.update_server_state(
                self.app_id,
                self.agent_id,
                [await msg.to_json() for msg in http_msgs],
                browser_actions,
            )

    def _update_state(self, result, model_output, step_info):
        """Update agent state with results from actions"""

        # random state update stuff ...
        for ret_ in result:
            if ret_.extracted_content and "Extracted page" in ret_.extracted_content:
                # record every extracted page
                if ret_.extracted_content[:100] not in self.state.extracted_content:
                    self.state.extracted_content += ret_.extracted_content

        self.state.last_result = result
        self.state.last_action = model_output.action
        if len(result) > 0 and result[-1].is_done:
            if not self.state.extracted_content:
                self.state.extracted_content = step_info.memory
            result[-1].extracted_content = self.state.extracted_content
            logger.info(f"📄 Result: {result[-1].extracted_content}")

        self.state.consecutive_failures = 0

    def create_or_update_plan(
        self,
        curr_page_contents: str,
        step_info: CustomAgentStepInfo,
        last_action: List[ActionModel],
    ):
        prev_page_contents, prev_plan = step_info.prev_page_contents, step_info.plan
        # TODO: we should also detect *intentional* page navigation to reset the plan
        # if no plan generate plan
        # only generate plan once we have navigated to a page
        if not step_info.plan and curr_page_contents:
            step_info.plan = generate_plan(self.llm, curr_page_contents)
            task = PLANNING_TASK_TEMPLATE.format(plan=step_info.plan)
            step_info.task = task

            logger.info(f"[PLAN] Generated plan: {step_info.plan}")
        elif step_info.plan:
            step_info.plan = update_plan(
                self.llm, curr_page_contents, prev_page_contents, prev_plan, last_action
            )
            task = PLANNING_TASK_TEMPLATE.format(plan=step_info.plan)
            step_info.task = task

            logger.info(f"[PLAN] Updated plan: {step_info.plan}")
        else:
            logger.info("[PLAN]: No task updates")

    @time_execution_async("--step")
    async def step(self, step_info: Optional[CustomAgentStepInfo] = None) -> bool:
        """Execute one step of the task"""
        logger.info(f"##############[ Step {self.state.n_steps} ]##############")
        state = None
        model_output = None
        result: list[ActionResult] = []
        step_start_time = time.time()
        tokens = 0
        browser_actions: Optional[BrowserActions] = None
        curr_page: str = ""
        curr_url: str = ""
        early_shutdown = False

        try:
            state = await self.browser_session.get_state_summary(
                cache_clickable_elements_hashes=False
            )
            page_contents = state.element_tree.clickable_elements_to_string(
                include_attributes=self.settings.include_attributes
            )
            browser_actions = BrowserActions()

            await self._raise_if_stopped_or_paused()

            # TODO: add results?
            # TODO: add page url?
            self.create_or_update_plan(
                page_contents,
                step_info, 
                self.state.last_action
            )

            self._message_manager.add_state_message(
                state,
                self.state.last_action,
                self.state.last_result,
                self.step_http_msgs,
                step_info=step_info,
                use_vision=self.settings.use_vision,
            )
            input_messages = self._message_manager.get_messages()

            logger.info(f"MESSAGE_LEN: {len(input_messages)}")
            for msg in input_messages:
                logger.info(f"MESSAGE: {type(msg)}")

            tokens = self._message_manager.state.history.current_tokens
            try:
                for msg in input_messages:
                    msg.type = ""
                model_output = await self.get_next_action(input_messages)
                self.update_step_info(model_output, step_info)
                # n_steps counts the number of total steps
                self.state.n_steps += 1
                await self._raise_if_stopped_or_paused()
                self._message_manager._remove_last_state_message()  # Remove state from chat history
            except Exception as e:
                self._message_manager._remove_last_state_message()
                logger.info(
                    f"LLM Parsing failed, here is the failure message => {input_messages[-1]}"
                )
                raise e

            result: list[ActionResult] = await self.multi_act(model_output.action)

            # EXECUTION ORDER CHANGE: Moving state update earlier to match reference pattern
            self.state.last_result = result

            # CustomAgent specific logic - preserving existing functionality
            curr_page = page_contents
            curr_url = (await self.browser_session.get_current_page()).url
            prev_url = curr_url
            prev_page = curr_page

            http_msgs = await self.http_handler.flush()
            self.step_http_msgs = self.http_history.filter_http_messages(http_msgs)
            browser_actions = BrowserActions(
                actions=model_output.action,
                thought=model_output.current_state.memory,
                goal=model_output.current_state.next_goal,
            )
            if self.agent_client:
                await self._update_server(self.step_http_msgs, browser_actions)
            if self.eval_client:
                early_shutdown = await self.eval_client.update_challenge_status(
                    step_info, self.step_http_msgs, browser_actions
                )

            # self._update_state(result, model_output, step_info)
            self._log_response(
                self.step_http_msgs,
                current_msg=input_messages[-1],
                response=model_output,
            )

            # Match reference pattern for completion logging
            if len(result) > 0 and result[-1].is_done:
                if not self.state.extracted_content:
                    self.state.extracted_content = step_info.memory
                result[-1].extracted_content = self.state.extracted_content
                logger.info(f"📄 Result: {result[-1].extracted_content}")

            self.state.consecutive_failures = 0

        except InterruptedError:
            logger.debug("Agent paused")
            self.state.last_result = [
                ActionResult(
                    error="The agent was paused - now continuing actions might need to be repeated",
                    include_in_memory=True,
                )
            ]
            return early_shutdown

        except Exception as e:
            # Match reference pattern - handle step errors
            logger.error(f"Error in step {self.state.n_steps}: {e}")
            logger.error(traceback.format_exc())

            # CustomAgent doesn't have _handle_step_error, so we'll create a similar pattern
            result = await self._handle_step_error(e, step_info)
            self.state.last_result = result

        finally:
            step_end_time = time.time()

            # Match reference pattern for history creation
            if state and result:  # Only create history if we have both state and result
                metadata = StepMetadata(
                    step_number=self.state.n_steps,
                    step_start_time=step_start_time,
                    step_end_time=step_end_time,
                    input_tokens=tokens,
                )
                json_msgs = [await msg.to_json() for msg in self.step_http_msgs]
                self._make_history_item(
                    model_output, state, result, json_msgs, metadata=metadata
                )

        return early_shutdown

    @time_execution_async("--handle_step_error (agent)")
    async def _handle_step_error(
        self, error: Exception, step_info: Optional[CustomAgentStepInfo] = None
    ) -> list[ActionResult]:
        """Handle all types of errors that can occur during a step"""
        include_trace = logger.isEnabledFor(logging.DEBUG)
        error_msg = AgentError.format_error(error, include_trace=include_trace)
        prefix = f"❌ Result failed {self.state.consecutive_failures + 1}/{self.settings.max_failures} times:\n "

        if isinstance(error, (ValidationError, ValueError)):
            logger.error(f"{prefix}{error_msg}")
            if "Max token limit reached" in error_msg:
                # cut tokens from history
                self._message_manager.settings.max_input_tokens = (
                    self.settings.max_input_tokens - 500
                )
                logger.info(
                    f"Cutting tokens from history - new max input tokens: {self._message_manager.settings.max_input_tokens}"
                )
                self._message_manager.cut_messages()
            elif "Could not parse response" in error_msg:
                # give model a hint how output should look like
                error_msg += "\n\nReturn a valid JSON object with the required fields."

            self.state.consecutive_failures += 1

        return [ActionResult(error=error_msg, include_in_memory=True)]

    async def run(self, max_steps: int = 100) -> AgentHistoryList:
        """Execute the task with maximum number of steps"""
        try:
            self._log_agent_run()

            # Execute initial actions if provided
            if self.initial_actions:
                result = await self.multi_act(
                    self.initial_actions, check_for_new_elements=False
                )
                self.state.last_result = result

            # TODO: not an ideal place to put task ...
            step_info = CustomAgentStepInfo(
                add_infos=self.add_infos,
                step_number=1,
                max_steps=max_steps,
                memory="",
                task=self.task,
                plan=None,
                prev_page_contents=None,
            )

            for step in range(max_steps):
                # Check if we should stop due to too many failures
                if self.state.consecutive_failures >= self.settings.max_failures:
                    logger.error(
                        f"❌ Stopping due to {self.settings.max_failures} consecutive failures"
                    )
                    break

                # Check control flags before each step
                if self.state.stopped:
                    logger.info("Agent stopped")
                    break

                while self.state.paused:
                    await asyncio.sleep(0.2)  # Small delay to prevent CPU spinning
                    if self.state.stopped:  # Allow stopping while paused
                        break

                shutdown = await self.step(step_info)
                if shutdown:
                    logger.info("Early shutdown")
                    break

                if self.state.history.is_done():
                    if self.settings.validate_output and step < max_steps - 1:
                        if not await self._validate_output():
                            continue

                    logger.info("Final response validated by agent")
                    await self.log_completion()
                    break
            else:
                logger.info("❌ Failed to complete task in maximum steps")
                if not self.state.extracted_content:
                    self.state.history.history[-1].result[
                        -1
                    ].extracted_content = step_info.memory
                else:
                    self.state.history.history[-1].result[
                        -1
                    ].extracted_content = self.state.extracted_content

            if self.history_file:
                self.state.history.save_to_file(self.history_file)

            return self.state.history

        finally:
            await self.shutdown(
                reason=f"Natural shutdown after [{step_info.step_number}/{step_info.max_steps}]"
            )

    async def shutdown(self, reason: str) -> None:
        """Shuts down the agent prematurely and performs cleanup."""
        # Check if already stopped to prevent duplicate shutdown calls
        if hasattr(self.state, "stopped") and self.state.stopped:
            logger.warning("Shutdown already in progress or completed.")
            return

        logger.info(f"Initiating premature shutdown: {reason}")
        # Ensure state has 'stopped' attribute before setting
        if hasattr(self.state, "stopped"):
            self.state.stopped = True
        else:
            # If AgentState doesn't have stopped, we might need another way
            # to signal termination or handle this case.
            logger.warning(
                "Agent state does not have 'stopped' attribute. Cannot signal stop."
            )

        # Perform cleanup similar to the finally block in run()
        try:
            # Capture Telemetry for Shutdown Event
            # Check existence of attributes before accessing due to potential type issues
            agent_id = getattr(self.state, "agent_id", "unknown_id")
            steps = getattr(self.state, "n_steps", 0)
            history = getattr(self.state, "history", None)
            errors = (history.errors() if history else []) + [f"Shutdown: {reason}"]
            input_tokens = history.total_input_tokens() if history else 0
            duration_seconds = history.total_duration_seconds() if history else 0.0

            # self.telemetry.capture(
            #     AgentEndTelemetryEvent(
            #         agent_id=agent_id,
            #         is_done=False, # Task was not completed normally
            #         success=False, # Assume failure on shutdown
            #         steps=steps,
            #         max_steps_reached=False,
            #         errors=errors,
            #         total_input_tokens=input_tokens,
            #         total_duration_seconds=duration_seconds,
            #     )
            # )

            # Save History
            if self.history_file and history:
                try:
                    history.save_to_file(self.history_file)
                    logger.info(
                        f"Saved agent history to {self.history_file} during shutdown."
                    )
                except Exception as e:
                    logger.error(f"Failed to save history during shutdown: {e}")

            # Close Browser Context
            if self.browser_context:
                try:
                    await self.browser_context.close()
                    logger.info("Closed browser context during shutdown.")
                except Exception as e:
                    logger.error(f"Error closing browser context during shutdown: {e}")

            # Close Browser
            if self.browser:
                try:
                    await self.browser.close()
                    logger.info("Closed browser during shutdown.")
                except Exception as e:
                    logger.error(f"Error closing browser during shutdown: {e}")

            # Generate GIF
            if self.settings.generate_gif and history:
                try:
                    output_path: str = "agent_history_shutdown.gif"  # Default name
                    if isinstance(self.settings.generate_gif, str):
                        # Create a shutdown-specific name based on config
                        base, ext = os.path.splitext(self.settings.generate_gif)
                        output_path = f"{base}_shutdown{ext}"

                    logger.info(f"Generating shutdown GIF at {output_path}")
                    create_history_gif(
                        task=f"{self.task} (Shutdown)",
                        history=history,
                        output_path=output_path,
                    )
                except Exception as e:
                    logger.error(f"Failed to generate GIF during shutdown: {e}")

        except Exception as e:
            # Catch errors during the shutdown cleanup process itself
            logger.error(f"Error during agent shutdown cleanup: {e}")
            logger.error(traceback.format_exc())
        finally:
            logger.info("Agent shutdown process complete.")
