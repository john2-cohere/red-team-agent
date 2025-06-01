import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence, Type, Literal
from pydantic import BaseModel
from browser_use.browser.profile import BrowserProfile
from browser_use.browser.session import BrowserSession

from src.agent.custom_agent import CustomAgent   # or wherever your agent lives

from .http_handler import HTTPHandler, BAN_LIST

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class AgentLogin(BaseModel):
    username: str | None = None
    email: str | None = None
    role: str
    password: str
    
    @classmethod
    def model_validator(cls, values):
        if not values.get("username") and not values.get("email"):
            raise ValueError("At least one of username or email must be provided")
        return values
    
# TEST spawning multiple browsers
class AgentHarness:
    """
    Spawns and supervises multiple CustomAgent instances, each with its own BrowserSession.
    """     

    def __init__(
        self,
        browser_profile_template: BrowserProfile,
        agents_config: Sequence[Dict[str, Any]],
        agent_cls: Type[CustomAgent] = CustomAgent,
        common_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.browser_profile_template = browser_profile_template
        self.agent_cls = agent_cls
        self.agents_cfg = list(agents_config or [])
        self.common_kwargs = common_kwargs or {}

        self._agents: List[CustomAgent] = []
        self._tasks: List[asyncio.Task] = []
        self.browser_sessions: List[BrowserSession] = []
        self._history: List[Dict] = []

        # Determine if browsers should be closed when the harness is done.
        self.close_browser_on_cleanup = self.common_kwargs.pop("close_browser", True)

    # ---------- public API -------------------------------------------------

    async def start_all(self, max_steps: int = 100):
        """
        Build and launch every agent, each with its own BrowserSession.
        Returns the list of asyncio.Tasks.
        """
        logger.info("Spawning %d agents …", len(self.agents_cfg))
        self._agents = []
        self.browser_sessions = []
        self._tasks = []
        self._history = [] # Reset history for this run
        
        for raw_cfg_item in self.agents_cfg:
            http_handler = HTTPHandler(banlist=BAN_LIST)

            # Prepare BrowserProfile for this specific agent's session
            current_agent_profile = self.browser_profile_template.model_copy()
            # The keep_alive on the profile tells the session whether to close the browser
            # when that specific session.stop() is called.
            # If close_browser_on_cleanup is True for the harness, we want the browser to die with the session.
            current_agent_profile.keep_alive = not self.close_browser_on_cleanup

            # Create and start a new BrowserSession for this agent
            session = BrowserSession(browser_profile=current_agent_profile)
            session.http_request_handler = http_handler.handle_request
            session.http_response_handler = http_handler.handle_response

            await session.start()

            self.browser_sessions.append(session)

            # Prepare agent configuration
            # Start with common_kwargs, then override with agent-specific raw_cfg_item
            agent_constructor_kwargs = {**self.common_kwargs, **raw_cfg_item}
            agent_constructor_kwargs['http_handler'] = http_handler

            # Pass the dedicated browser_session to the agent
            agent_constructor_kwargs['browser_session'] = session

            # Remove keys that are now handled by BrowserProfile/BrowserSession
            # and should not be passed directly to the Agent if it expects a browser_session.
            # Example: if CustomAgent previously took 'browser_profile' or 'context_cfg'
            agent_constructor_kwargs.pop('browser_profile', None)
            agent_constructor_kwargs.pop('context_cfg', None) 
            agent_constructor_kwargs.pop('browser', None) # Ensure no old browser object is passed
            # Add any other keys that CustomAgent should not receive when a session is provided.

            # Instantiate and launch the agent
            # Assuming CustomAgent's __init__ is something like: (self, task, llm, browser_session, **other_kwargs)
            # Adjust if your CustomAgent takes browser_session differently or has other required positional args.
            agent = self.agent_cls(**agent_constructor_kwargs)
            self._agents.append(agent)

            task = asyncio.create_task(self._run_agent(agent, max_steps))
            self._tasks.append(task)

        return self._tasks

    async def wait(self):
        done, _ = await asyncio.wait(self._tasks, return_when=asyncio.ALL_COMPLETED)
        for t in done:
            if exc := t.exception():
                logger.error("Agent task raised: %s", exc)

    async def kill_all(self, reason: str = "kill"):
        """
        Stops every agent, cancels outstanding tasks, and closes all contexts
        created by the harness.
        """
        logger.warning("Kill‑switch activated: %s", reason)

        # Ask agents to shut down gracefully
        # If agent.shutdown is not async or doesn't exist, this needs adjustment.
        # Assuming agent.shutdown exists and is a coroutine based on original code.
        if self._agents:
            await asyncio.gather(
                *(agent.shutdown(reason) for agent in self._agents if hasattr(agent, 'shutdown')),
                return_exceptions=True,
            )

        # Cancel any lingering tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to acknowledge cancellation (optional but good practice)
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close BrowserSessions that *we* created
        for session in self.browser_sessions:
            try:
                if session and session.initialized: # Check if session exists and was started
                    await session.stop() # session.stop() respects profile.keep_alive
            except Exception as e:
                logger.debug("BrowserSession close failed: %s", e)
        
        # Clear lists
        self._agents = []
        self._tasks = []
        self.browser_sessions = []
        # self._history is typically kept until a new run, or cleared by start_all

    # ---------- helpers ----------------------------------------------------

    async def _run_agent(self, agent: CustomAgent, max_steps: int):
        try:
            history = await agent.run(max_steps=max_steps)
            self._history.append(history.model_dump())
        except asyncio.CancelledError:
            logger.info("Agent cancelled")
        except Exception as e:
            logger.exception("Agent crashed: %s", e)

    def get_history(self):
        """
        Returns the history of all agents.
        """
        def remove_screenshots(d):
            if isinstance(d, dict):
                return {k: remove_screenshots(v) for k, v in d.items() if k != "screenshot"}
            elif isinstance(d, list):
                return [remove_screenshots(x) for x in d]
            return d
            
        return remove_screenshots(self._history)
