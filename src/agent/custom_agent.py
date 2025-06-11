import json
from this import d
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
    Tuple,
    TypeVar,
    Set,
    Deque,
    Union,
)
import os
import asyncio
import time
from enum import Enum, nonmember
from langchain.schema import AIMessage
from numpy import int16
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
from src.utils import retry_async, RetryError, EarlyShutdown

from eval.ctf_server.client import EvalClient

from johnllm import LLMModel, LMP
from httplib import HTTPRequest, HTTPResponse, HTTPMessage

from logging import getLogger

# from .state import CustomAgentOutput
from pentest_bot.agent.logger import setup_agent_logger
from common.agent import BrowserActions
from .custom_views import CustomAgentOutput
from .custom_message_manager import CustomMessageManager, CustomMessageManagerSettings
from .custom_views import CustomAgentStepInfo, CustomAgentState
from .http_handler import HTTPHistory, HTTPHandler
from .logger import AgentLogger
from .discovery import (
    update_plan, 
    generate_plan, 
    determine_new_page,
    check_plan_completion,
    NewPageStatus, 
    NavigationPage,
    PLANNING_TASK_TEMPLATE,
    UNDO_NAVIGATION_TASK_TEMPLATE
)

logger = getLogger(__name__)

Context = TypeVar("Context")

DEFAULT_INCLUDE_MIME = ["html", "script", "xml", "flash", "other_text"]
DEFAULT_INCLUDE_STATUS = ["2xx", "3xx", "4xx", "5xx"]
MAX_PAYLOAD_SIZE = 4000
DEFAULT_FLUSH_TIMEOUT = 5.0  # seconds to wait for all requests to be flushed
DEFAULT_PER_REQUEST_TIMEOUT = 2.0  # seconds to wait for *each* unmatched request
DEFAULT_SETTLE_TIMEOUT = 1.0  # seconds of network "silence" after the *last* response
POLL_INTERVAL = 0.5  # how often we poll internal state

# class SubPage:
#     url: str
#     page_contents: str
#     name: str

# class Page(BaseModel):
#     # name: str ???
#     url: str
#     homepage: str
#     subpages: List[SubPage]

# class AgentNavigationState(BaseModel):
#     curr_page: 
#     all_pages: List[Page]

class LLMClients(str, Enum):
    COHERE = "cohere"
    DEEPSEEK = "deepseek"
    DEEPSEEK_REASONER = "deepseek_reasoner"

# Planning Agent:
# - need to detect when page has changed to
class CustomAgent(Agent):
    def __init__(
        self,
        task: str,
        agent_name: str,
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
        print(f"Setting up agent logger for {agent_name}")
        self.agent_log, self.full_log = self._init_loggers(agent_name)
        
        self.homepage_url = ""
        self.homepage_contents = ""

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

        self.state = CustomAgentState(task=task)
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

    def get_agent_state(self) -> CustomAgentState:
        return self.state

    def _init_loggers(self, log_name: str = "default-agent"):
        agent_log, full_log = setup_agent_logger(log_name, log_name=log_name)

        def log_agent(msg: str):
            agent_log.info(msg)

        def log_full_requests(msg: str):
            agent_log.info(msg)
            full_log.info(msg)

        return log_agent, log_full_requests

    def handle_page(self, page):
        self.full_log(f"[PLAYWRIGHT] >>>>>>>>>>>")
        self.full_log(f"[PLAYWRIGHT] Frame {page}")
        self.curr_page = page

    def _log_response(
        self,
        http_msgs: List[HTTPMessage],
        current_msg: BaseMessage,
        response: CustomAgentOutput,
        curr_goal: str,
        curr_url: str,
    ) -> None:
        """Log the model's response"""
        if "Success" in response.current_state.evaluation_previous_goal:
            emoji = "✅"
        elif "Failed" in response.current_state.evaluation_previous_goal:
            emoji = "❌"
        else:
            emoji = "🤷"

        self.agent_log(f"🌐 Current URL: {curr_url}")
        self.agent_log(f"🎯 Current Goal: {curr_goal}")
        self.agent_log(f"{emoji} Eval: {response.current_state.evaluation_previous_goal}")
        # self.full_log(f"🧠 New Memory: {response.current_state.important_contents}")
        # self.full_log(f"🤔 Thought: {response.current_state.thought}")
        self.agent_log(f"🎯 Next Goal: {response.current_state.next_goal}")
        for i, action in enumerate(response.action):
            self.agent_log(
                f"🛠️  Action {i + 1}/{len(response.action)}: {action.model_dump_json(exclude_unset=True)}"
            )
        self.agent_log(f"[Message]: {current_msg.content}")
        self.agent_log(f"Captured {len(http_msgs)} HTTP Messages")
        for msg in http_msgs:
            self.full_log(f"[Agent] {msg.request.url}")

    def update_step_info(
        self,
        model_output: CustomAgentOutput,
        step_info: CustomAgentStepInfo,
        curr_url: str,
        page_contents: str
    ):
        """
        update step info
        """
        if step_info is None:
            return

        step_info.step_number += 1
        # step_info.prev_url = curr_url
        # step_info.prev_page_contents = page_contents
        # important_contents = model_output.current_state.important_contents
        # if (
        #         important_contents
        #         and "None" not in important_contents
        #         and important_contents not in step_info.memory
        # ):
        #     step_info.memory += important_contents + "\n"

        self.agent_log(f"🧠 All Memory: \n{step_info.memory}")

    @time_execution_async("--get_next_action")
    async def get_next_action(
        self, input_messages: List[BaseMessage]
    ) -> Tuple[CustomAgentOutput, AIMessage]:
        """Get next action from LLM based on current state"""
        ai_message = self.llm.invoke(
            input_messages,
        )
        # for tracking message history
        # self._message_manager._add_message_with_tokens(ai_message)
        ai_content = ai_message.content.replace("```json", "").replace("```", "")
        ai_content = repair_json(ai_content)
        parsed_json = json.loads(ai_content)
        self.full_log(f"[PARSED]: {parsed_json}")

        parsed: AgentOutput = self.AgentOutput(**parsed_json)

        if parsed is None:
            logger.debug(ai_message.content)
            raise ValueError("Could not parse response.")

        # cut the number of actions to max_actions_per_step if needed
        if len(parsed.action) > self.settings.max_actions_per_step:
            parsed.action = parsed.action[: self.settings.max_actions_per_step]
        return parsed, ai_message

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

    def _update_state(
        self,
        result: List[ActionResult],
        model_output: CustomAgentOutput,
        step_info: CustomAgentStepInfo,
        page_contents: str,
        curr_url: str,
        next_goal: str, 
    ):
        """Update agent state with results from actions"""

        # for ret_ in result:
        #     if ret_.extracted_content and "Extracted page" in ret_.extracted_content:
        #         # record every extracted page
        #         if ret_.extracted_content[:100] not in self.state.extracted_content:
        #             self.state.extracted_content += ret_.extracted_content
        self.state.n_steps += 1
        self.state.prev_page_contents = page_contents
        self.state.prev_url = curr_url
        self.state.last_result = result
        self.state.prev_goal = next_goal

        self.state.last_action = model_output.action
        self.state.eval_prev_goal = model_output.current_state.evaluation_previous_goal

        if len(result) > 0 and result[-1].is_done:
            if not self.state.extracted_content:
                self.state.extracted_content = step_info.memory
            result[-1].extracted_content = self.state.extracted_content
            self.agent_log(f"📄 Result: {result[-1].extracted_content}")

        self.state.consecutive_failures = 0

    async def create_or_update_plan(
        self,
        curr_page_contents: str,
        cur_url: str,
        step_number: int
    ) -> Tuple[str, Optional[str]]:
        prev_page_contents = self.state.prev_page_contents
        curr_plan = self.state.plan
        prev_url = self.state.prev_url
        eval_prev_goal = self.state.eval_prev_goal
        prev_goal = self.state.prev_goal

        if step_number == 1:
            return self.state.task, None

        # TODO: we should also detect *intentional* page navigation to reset the plan
        # if no plan generate plan
        # only generate plan once we have navigated to a page
        # skip the browser intiializtion phase where the
        if not curr_plan and curr_page_contents and not prev_page_contents:
            curr_plan = generate_plan(self.llm, curr_page_contents)
            self.state.plan = curr_plan
            new_task = PLANNING_TASK_TEMPLATE.format(plan=curr_plan)

            # init homepage
            self.homepage_url = cur_url
            self.homepage_contents = curr_page_contents
            self.state.pages.append(cur_url)
            
            self.full_log(f"[PLAN] Generated plan: {curr_plan}")
            return new_task, None
        
        self.agent_log(f"[SUBPAGES]: {[page[2] for page in self.state.subpages]}")

        # TODO: parallelize these two
        curr_plan = check_plan_completion(
            self.llm, 
            curr_plan, 
            prev_page_contents, 
            curr_page_contents, 
            prev_goal
        )
        self.state.plan = curr_plan
        nav_page = determine_new_page(
            self.llm, 
            curr_page_contents, 
            prev_page_contents, 
            cur_url, 
            prev_url, 
            prev_goal, 
            self.state.subpages,
            self.homepage_contents,
            self.homepage_url
        )

        # TODO: we need to be careful to check that the last plan is not a back navigation task
        if nav_page.page_type == NewPageStatus.NEW_PAGE:
            new_task = UNDO_NAVIGATION_TASK_TEMPLATE.format(
                prev_url=prev_url,
                prev_page_contents=prev_page_contents
            )
            self.state.pages.append(cur_url)

            self.agent_log(f"[PLAN]: New page, navigating back from {cur_url}")
            return new_task, self.state.task

        elif nav_page.page_type == NewPageStatus.UPDATED_PAGE:
            # TODO: maybe need to rework should backnavigation to be smarter than default to back-navigation
            # -> ties into how we should use memory -> remembering back-navigation from page
            # TODO: need to set a status for when we navigate back from a page
            # TODO: compare to naive results
            # TODO: explicitly tell it to use nested subplan structure
            # TODO: tell it to not to refer to interactive elements by their index
            curr_plan = update_plan(
                self.llm, curr_page_contents, prev_page_contents, curr_plan, self.state.eval_prev_goal
            )
            self.state.plan = curr_plan
            new_task = PLANNING_TASK_TEMPLATE.format(plan=curr_plan)
            self.state.subpages.append((cur_url, curr_page_contents, nav_page.name))

            self.agent_log(f"[PLAN] Updated plan: {curr_plan}")
            return new_task, None
        else:
            self.agent_log("[PLAN]: No task updates")
            # return the old task
            return self.state.task, None

    @time_execution_async("--step")
    async def step(self, step_info: Optional[CustomAgentStepInfo] = None) -> bool:
        """Execute one step of the task"""
        self.agent_log(f"##############[ Step {self.state.n_steps} ]##############")
        state = None
        model_output = None
        result: list[ActionResult] = []
        step_start_time = time.time()
        tokens = 0
        browser_actions: Optional[BrowserActions] = None
        early_shutdown = False

        try:
            # NOTE: this is state of the playwright browser, not to be confused with self.state
            # which represents state of the agent
            state = await self.browser_session.get_state_summary(cache_clickable_elements_hashes=False)
            page_contents = state.element_tree.clickable_elements_to_string(include_attributes=self.settings.include_attributes)
            curr_url = (await self.browser_session.get_current_page()).url
            browser_actions = BrowserActions()

            await self._raise_if_stopped_or_paused()

            # TODO: should maybe move homepage init out of here?
            new_task, replace_task = await self.create_or_update_plan(
                page_contents,
                curr_url,
                step_info.step_number
            )
            self.state.task = new_task

            self._message_manager.add_state_message(
                state,
                self.state.last_action,
                self.state.last_result,
                self.step_http_msgs,
                self.state.task,
                step_info=step_info,
                use_vision=self.settings.use_vision,
            )
            input_messages = self._message_manager.get_messages()
            tokens = self._message_manager.state.history.current_tokens
            try:
                # HACK:
                for msg in input_messages:
                    msg.type = ""
                model_output, output_msg = await self.get_next_action(input_messages)

                # NOTE: we remove all of message requests but we keep all of the model outputs
                # as chat history
                self._message_manager._remove_last_state_message()
                self._message_manager._add_message_with_tokens(output_msg)
                self.full_log(f"MESSAGE_LEN: {len(input_messages)}")
                for msg in input_messages:
                    self.full_log(f"MESSAGE: {type(msg)}")

                self.update_step_info(model_output, step_info, curr_url, page_contents)
                # update the state
                await self._raise_if_stopped_or_paused()

                self.full_log(f"MESSAGE_LEN AFTER: {len(self._message_manager.get_messages())}")
            except Exception as e:
                self._message_manager._remove_last_state_message()
                self.full_log(
                    f"LLM Parsing failed, here is the failure message => {input_messages[-1]}"
                )
                raise e

            result: list[ActionResult] = await self.multi_act(model_output.action)

            http_msgs = await self.http_handler.flush()
            self.step_http_msgs = self.http_history.filter_http_messages(http_msgs)
            browser_actions = BrowserActions(
                actions=model_output.action,
                thought=model_output.current_state.memory,
                goal=model_output.current_state.next_goal,
            )
            if self.agent_client:
                await self._update_server(self.step_http_msgs, browser_actions)
                
            self._update_state(
                result, 
                model_output, 
                step_info, 
                page_contents, 
                curr_url, 
                model_output.current_state.next_goal
            )
            self._log_response(
                self.step_http_msgs,
                current_msg=input_messages[-1],
                response=model_output,
                curr_goal=self.state.prev_goal,
                curr_url=curr_url,
            )

            # Match reference pattern for completion logging
            if len(result) > 0 and result[-1].is_done:
                if not self.state.extracted_content:
                    self.state.extracted_content = step_info.memory
                result[-1].extracted_content = self.state.extracted_content
                self.agent_log(f"📄 Result: {result[-1].extracted_content}")

            self.state.consecutive_failures = 0
            
            # TODO: really bug here:
            # - if replace
            if replace_task:
                self.state.task = replace_task

            if self.eval_client:
                early_shutdown = await self.eval_client.update_challenge_status(
                    step_info.step_number, self.step_http_msgs, browser_actions
                )

        except (InterruptedError, EarlyShutdown):
            self.agent_log("Shutdown called by agent")
            self.state.last_result = [
                ActionResult(
                    error="The agent was paused - now continuing actions might need to be repeated",
                    include_in_memory=True,
                )
            ]
            early_shutdown = True
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
            self.full_log(f"{prefix}{error_msg}")
            if "Max token limit reached" in error_msg:
                # cut tokens from history
                self._message_manager.settings.max_input_tokens = (
                    self.settings.max_input_tokens - 500
                )
                self.full_log(
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
            )

            for step in range(max_steps):
                # Check if we should stop due to too many failures
                if self.state.consecutive_failures >= self.settings.max_failures:
                    self.agent_log(
                        f"❌ Stopping due to {self.settings.max_failures} consecutive failures"
                    )
                    break

                # Check control flags before each step
                if self.state.stopped:
                    self.agent_log("Agent stopped")
                    break

                while self.state.paused:
                    await asyncio.sleep(0.2)  # Small delay to prevent CPU spinning
                    if self.state.stopped:  # Allow stopping while paused
                        break

                shutdown = await self.step(step_info)
                if shutdown:
                    self.agent_log("Early shutdown")
                    break

                # TODO: honestly dont quite understand the logic here but knows that it triggers early shutdown
                # if self.state.history.is_done():
                #     if self.settings.validate_output and step < max_steps - 1:
                #         if not await self._validate_output():
                #             continue

                #     logger.info("Final response validated by agent")
                #     await self.log_completion()
                #     break
            else:
                self.agent_log("❌ Failed to complete task in maximum steps")
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

        self.agent_log(f"Initiating premature shutdown: {reason}")
        # Ensure state has 'stopped' attribute before setting
        if hasattr(self.state, "stopped"):
            self.state.stopped = True
        else:
            # If AgentState doesn't have stopped, we might need another way
            # to signal termination or handle this case.
            self.agent_log(
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
                    self.agent_log(
                        f"Saved agent history to {self.history_file} during shutdown."
                    )
                except Exception as e:
                    self.agent_log(f"Failed to save history during shutdown: {e}")

            # Close Browser Context
            if self.browser_context:
                try:
                    await self.browser_context.close()
                    self.agent_log("Closed browser context during shutdown.")
                except Exception as e:
                    self.agent_log(f"Error closing browser context during shutdown: {e}")

            # Close Browser
            if self.browser:
                try:
                    await self.browser.close()
                    self.agent_log("Closed browser during shutdown.")
                except Exception as e:
                    self.agent_log(f"Error closing browser during shutdown: {e}")

            # Generate GIF
            if self.settings.generate_gif and history:
                try:
                    output_path: str = "agent_history_shutdown.gif"  # Default name
                    if isinstance(self.settings.generate_gif, str):
                        # Create a shutdown-specific name based on config
                        base, ext = os.path.splitext(self.settings.generate_gif)
                        output_path = f"{base}_shutdown{ext}"

                    self.agent_log(f"Generating shutdown GIF at {output_path}")
                    create_history_gif(
                        task=f"{self.task} (Shutdown)",
                        history=history,
                        output_path=output_path,
                    )
                except Exception as e:
                    self.agent_log(f"Failed to generate GIF during shutdown: {e}")

        except Exception as e:
            # Catch errors during the shutdown cleanup process itself
            self.agent_log(f"Error during agent shutdown cleanup: {e}")
            self.agent_log(traceback.format_exc())
        finally:
            self.agent_log("Agent shutdown process complete.")

