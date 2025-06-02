import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from uuid import UUID
from httpx import AsyncClient
from pydantic import BaseModel

from src.agent.client import AgentClient
from common.agent import BrowserActions

from eval.challenges import Challenge

logger = logging.getLogger(__name__)


class VulnAppClient(AgentClient):
    """
    Thin wrapper around `AgentClient` that knows how to:

      • keep a catalogue of *all* vulnerabilities exposed by the target app
      • track which subset we care about (`_targeted_vulns`)
      • poll the target app's `/api/Challenges` endpoint and mark completion
    """

    # --------------------------- life‑cycle --------------------------------

    def __init__(
        self,
        *,
        vuln_client: AsyncClient,
        targeted_vulns: List[Challenge] = None,
        all_vulns: List[Challenge] = None,
        **kwargs,
    ):
        """
        Parameters
        ----------
        vuln_client
            Pre‑configured httpx.AsyncClient that speaks to the vulnerable app
            (e.g. OWASP Juice Shop running at http://127.0.0.1:3000).
        targeted_vulns
            Subset of `all_vulns` the pentest run should try to exploit.
            If empty or None, no completion checking will occur.
        all_vulns
            Full list of vulnerabilities the app *could* expose.
        kwargs
            Forwarded verbatim to the parent `AgentClient`.
        """
        super().__init__(**kwargs)

        self._vuln_client = vuln_client
        self._steps = 0

        # Handle empty lists
        targeted_vulns = targeted_vulns or []
        all_vulns = all_vulns or []

        # Dict[int, Challenge] for O(1) lookups by ID
        self._all_vulns: Dict[int, Challenge] = {v.id: v for v in all_vulns}

        # Keep *objects* for the subset we target
        self._targeted_vulns: List[Challenge] = targeted_vulns

        self._shutdown: Callable = None
    
        # Sanity check: every target must exist in the global list
        # Skip check if no targets are specified
        if targeted_vulns:
            non_exist = self._check_target_vulns()
            if non_exist:
                raise ValueError(f"Targeted vulns do not exist: {non_exist}")
            logger.info("Target set: %s", [v.id for v in targeted_vulns])
        else:
            logger.info("No targets specified - completion checking disabled")

    # ---------------------------------------------------------------------

    def _check_target_vulns(self) -> List[int]:
        """Return IDs that are in `_targeted_vulns` but not in `_all_vulns`."""
        return [v.id for v in self._targeted_vulns if v.id not in self._all_vulns]

    # ---------------------------------------------------------------------
    # Remote helpers
    # ---------------------------------------------------------------------

    async def get_challenges(self) -> Dict[str, Any]:
        """
        GET /api/Challenges from the vulnerable application.
        The Juice Shop flavour returns `{"status": "success", "data": [...]}`.
        """
        resp = await self._vuln_client.get("/api/Challenges")
        resp.raise_for_status()
        return resp.json()

    # ---------------------------------------------------------------------
    # Completion tracking
    # ---------------------------------------------------------------------

    def _update_completion_flags(self, challenges: Dict[str, Any]) -> List[Challenge]:
        # If no targets specified, return empty list
        if not self._targeted_vulns:
            return []
            
        solved_by_id = {item["id"]: item["solved"]
                        for item in challenges.get("data", [])}

        newly_solved: List[Challenge] = []
        for vuln in self._targeted_vulns:
            api_solved = solved_by_id.get(vuln.id, False)
            if api_solved and not vuln.solved:
                vuln.solved = True
                newly_solved.append(vuln)          # collect delta
        return newly_solved

    def all_targets_solved(self) -> bool:
        """True iff every targeted Challenge has solved == True."""
        # If no targets specified, always return False
        if not self._targeted_vulns:
            return False
        return all(vuln.solved for vuln in self._targeted_vulns)

    # ---------------------------------------------------------------------
    # Public API used by test harness / ageents
    # ---------------------------------------------------------------------
    async def update_server_state(self,
                                app_id: UUID,
                                agent_id: UUID,
                                messages: List[Dict[str, Any]],
                                browser_actions: Optional[List[BrowserActions]] ) -> Dict[str, int]:
        # 1. fire‑and‑forget – don't wait for the push
        asyncio.create_task(self.push_messages(app_id, agent_id, messages, browser_actions))

        # 2. pull latest challenge data
        challenges = await self.get_challenges()

        # 3. refresh flags and get the *new* ones
        newly_solved = self._update_completion_flags(challenges)

        # --- progress & highlight logs --------------------------------------
        for vuln in newly_solved:
            logger.info("### NEWLY SOLVED TARGET %s – %s ###", vuln.id, vuln.name)

        # If no targets specified, return empty status
        if not self._targeted_vulns:
            return {"solved_targets": 0, "remaining": 0}
            
        solved     = sum(vuln.solved for vuln in self._targeted_vulns)
        remaining  = len(self._targeted_vulns) - solved
        logger.info("Progress: %d / %d targets solved (%d remaining)",
                    solved, len(self._targeted_vulns), remaining)

        # 4. graceful shutdown when done
        if remaining == 0:
            logger.info("All targeted vulnerabilities solved – shutting down.")
            if callable(self._shutdown):
                await self._shutdown()

        # 5. short status dict for callers
        return {"solved_targets": solved, "remaining": remaining}
