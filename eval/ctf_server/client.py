import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic

from browser_use.agent.service import Agent
from browser_use.agent.views import AgentStepInfo

from common.agent import BrowserActions
from httplib import HTTPMessage
from pentest_bot.agent.logger import AgentLogLevels

from eval.challenges import Challenge

logger = logging.getLogger(AgentLogLevels.AGENT)

ChallengeType = TypeVar('ChallengeType', bound=Challenge)

class EvalClient(Generic[ChallengeType]):
    def __init__(
        self,
        *,
        targeted_vulns: List[ChallengeType] = None,
        max_steps: int = 12,
        **kwargs,
    ):
        self._steps = 0
        self._max_steps = max_steps
        self._targeted_vulns: List[ChallengeType] = targeted_vulns
        self._shutdown: Callable = None
        # TODO: kind of jank to not initialize this in the constructor
        self._agent_state: Any = None

        logger.info(f"Starting EvalClient with {self._max_steps} steps")

    @property
    def max_steps(self):
        return self._max_steps

    def set_shutdown(self, shutdown: Callable) -> None:
        """
        Set a shutdown function to be called when the agent is done.
        """
        self._shutdown = shutdown

    def set_agent_state(self, agent_state: Any) -> None:
        """
        Set the agent state to be used for the eval.
        """
        self._agent_state = agent_state

    def all_targets_solved(self, steps_taken: int) -> bool:
        """True iff every targeted Challenge has solved == True."""
        solved = False

        if not self._targeted_vulns:
            return False
        if steps_taken >= self._max_steps:
            logger.info(f"[EVAL]: Stopping due to {self._max_steps} hit")
            solved = True
        if all(vuln.solved for vuln in self._targeted_vulns):
            solved = True

        return solved

    async def check_completion(
        self,
        http_msgs: List[HTTPMessage], 
        browser_actions: List[BrowserActions]
    ):
        """Checks if new challenges have been completed"""
        pass

    def log_completion(self):
        # Print status of completed and missing vulnerabilities
        solved_vulns = [v for v in self._targeted_vulns if v.solved]

        logger.info("[EVAL]: === Vulnerability Status ===")
        logger.info(f"[EVAL]: Completed ({len(solved_vulns)}/{len(self._targeted_vulns)}):")       

    async def update_challenge_status(
        self,
        steps_taken: int,
        http_msgs: List[HTTPMessage],
        browser_actions: List[BrowserActions]
    ):
        await self.check_completion(http_msgs, browser_actions)
        if self.all_targets_solved(steps_taken):
            self.log_completion()

            await self._shutdown(reason="Shutdown after completing evals")
            return True

        return False