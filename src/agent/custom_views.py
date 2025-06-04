from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Type
import uuid

from browser_use.agent.views import (
    AgentStepInfo,
    AgentOutput,  
    ActionResult, 
    AgentHistoryList, 
    MessageManagerState
)
from browser_use.controller.registry.views import ActionModel
from pydantic import BaseModel, Field, create_model

from .discovery import Plan

@dataclass
class CustomAgentStepInfo(AgentStepInfo):
    step_number: int
    max_steps: int
    task: str
    add_infos: str
    memory: str
    plan: Optional[Plan]
    prev_page_contents: Optional[str]

class CustomAgentBrain(BaseModel):
    """Current state of the agent"""

    evaluation_previous_goal: str
    important_contents: str
    thought: str
    next_goal: str


class CustomAgentOutput(AgentOutput):
    """Output model for agent

    @dev note: this model is extended with custom actions in AgentService. You can also use some fields that are not in this model as provided by the linter, as long as they are registered in the DynamicActions model.
    """

    current_state: CustomAgentBrain
 
    @staticmethod
    def type_with_custom_actions(
            custom_actions: Type[ActionModel],
    ) -> Type["CustomAgentOutput"]:
        """Extend actions with custom actions"""
        model_ = create_model(
            "CustomAgentOutput",
            __base__=CustomAgentOutput,
            action=(
                list[custom_actions],
                Field(..., description='List of actions to execute', json_schema_extra={'min_items': 1}),
            ),  # Properly annotated field with no default
            __module__=CustomAgentOutput.__module__,
        )
        model_.__doc__ = 'AgentOutput model with custom actions'
        return model_


class CustomAgentState(BaseModel):
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    n_steps: int = 1
    consecutive_failures: int = 0
    last_result: List['ActionResult'] = Field(default_factory=list)
    history: AgentHistoryList = Field(default_factory=lambda: AgentHistoryList(history=[]))
    paused: bool = False
    stopped: bool = False
    extracted_content: str = ''
    message_manager_state: MessageManagerState = Field(default_factory=MessageManagerState)
    
    last_plan: Optional[str] = None
    last_action: List['ActionModel'] = Field(default_factory=list)
    last_page: Optional[str] = None
