import asyncio
import os
import traceback
import sys
from logging import getLogger

from langchain_cohere import ChatCohere
from browser_use.browser.profile import BrowserProfile
from src.agent.harness import AgentHarness
from src.agent.custom_prompts import CustomAgentMessagePrompt

from eval.ctf_server.client import EvalClient
from src.llm_providers import llm_providers, LLMProviders

logger = getLogger(__name__)

API_KEY = os.getenv("COHERE_API_KEY")

async def start_agent(
        agent_name: str,
        task: str, 
        max_steps: int = 15, 
        headless: bool = False,
        **agent_args,
    ) -> None:
    """
    Start a browser agent with the given task.
    
    Parameters
    ----------
    task : str
        The task/prompt for the agent to execute
    max_steps : int, optional
        Maximum number of steps for the agent (default: 15)
    headless : bool, optional
        Whether to run browser in headless mode (default: False)
    """
    
    # Initialize LLM
    # llm = ChatCohere(model="command-a-03-2025", cohere_api_key=API_KEY)
    # llm = LLM_PROVIDERS["cohere"]
    llm = llm_providers

    # Browser configuration
    browser_profile = BrowserProfile(
        no_viewport=False,
        headless=headless,
        disable_security=True,
    )

    # Agent configuration
    shared_cfg = {
        "llm": llm,
        "use_vision": False,
        "agent_prompt_class": CustomAgentMessagePrompt,
        "app_id": None,
        "close_browser": True,
        "agent_name": agent_name,
    }
    shared_cfg = { **shared_cfg, **agent_args }
    
    # Create agent harness
    harness = AgentHarness(
        browser_profile_template=browser_profile,
        agents_config=[{"task": task, "agent_client": None}],
        common_kwargs=shared_cfg,
    )
        
    try:
        # HACK: when eval_client.max_steps == agent.max_steps, agent always terminates first instead
        # whereas we want the eval_client to control termination
        await harness.start_all(max_steps=max_steps + 5)
        
        eval_client: EvalClient = shared_cfg.get("eval_client", None)
        if eval_client:
            agent = harness.get_agents()[0]
            eval_client.set_agent_state(agent.get_agent_state())
            eval_client.set_max_steps(max_steps)

        await harness.wait()
        logger.info("Agent task completed successfully")
        
        if eval_client:
            return eval_client.get_agent_results()
        else:
            return None
                
    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
        traceback.print_exc(file=sys.stderr)
        raise
        
    finally:
        logger.info("Shutting down agent")
        await harness.kill_all("Task completed")