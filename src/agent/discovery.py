import enum
import json
import difflib
import uuid
from typing import List, Dict, ClassVar, Optional, Tuple
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from langchain_core.language_models.chat_models import BaseChatModel
from browser_use.controller.registry.views import ActionModel
from browser_use.agent.views import ActionResult

from src.utils import dump_llm_messages_pretty, retry_sync, EarlyShutdown

from pentest_bot.agent.logger import AgentLogLevels
from logging import getLogger

full_logger = getLogger(AgentLogLevels.FULL_REQUESTS)
agent_logger = getLogger(AgentLogLevels.AGENT)

UNDO_NAVIGATION_TASK_TEMPLATE = """
You have successfully visited the new page

Your goal is now to return back to the previous page

Here is the previous page:
URL: {prev_url}
{prev_page_contents}
"""

PLANNING_TASK_TEMPLATE = """
Your task is to fully explore and discover every single page of a web application
To accomplish this, you should try to trigger as many functionalities on the current page as possible

Your goal is to discover the following elements on this page:
1. outgoing_links: links to other pages of the same web application
2. backend_calls: requests made to backend API services

You can find both by interacting with the webpage
Here are some strategies to guide your interaction:
- do not interact with elements that you suspect will trigger a navigation action off of the page
- elements on the page may be hidden, and to interact with them, you may have to perform some action such as expanding a submenu  

If you find that, after clicking on one of the outbound links, you are on *new* page, then immediately go back to your previous page if there are unfinished tasks there  

Here is the plan:
{plan}
"""

class PlanItem(BaseModel):
	"""A single actionable step in the exploration plan."""
	plan: str
	completed: bool = False
	id: str = Field(default_factory=lambda: str(uuid.uuid4()), exclude=True)

	model_schema: ClassVar[Dict] = {
		"type": "object",
		"required": ["plan"],
		"properties": {
			"plan": {
				"type": "string",
				"description": "The plan item description"
			},
			"completed": {
				"type": "boolean",
				"default": False,
				"description": "Whether the plan item is completed"
			}
		}
	}

	def __str__(self) -> str:  # noqa: D401
		repr_str = self.plan.replace("[ ] ", "")
		checkbox = "[*]" if self.completed else "[ ]"
		return f"{checkbox}   {repr_str}"


class Plan(BaseModel):
	plan_items: List[PlanItem]

	model_schema: ClassVar[Dict] = {
		"type": "json_object",
		"schema": {
			"type": "object",
			"required": ["plan_items"],
			"properties": {
				"plan_items": {
					"type": "array",
					"items": PlanItem.model_schema,
				},
			},
		},
	}

	def __str__(self) -> str:  # noqa: D401
		repr_str = "\n"
		for i, plan_item in enumerate(self.plan_items):
			checkbox = "[*]" if plan_item.completed else "[ ]"
			repr_str += f"{i}) {checkbox}   {plan_item.plan}\n"
		return repr_str


class AddPlanItem(BaseModel):
	plan_item: PlanItem
	index: int

	model_schema: ClassVar[Dict] = {
		"type": "object",
		"schema": {
			"type": "object",
			"required": ["plan_item", "index"],
			"properties": {
				"plan_item": PlanItem.model_schema,
				"index": {"type": "integer"},
			},
		},
	}


class DeletePlanItem(BaseModel):
	index: int

	model_schema: ClassVar[Dict] = {
		"type": "object",
		"schema": {
			"type": "object",
			"required": ["index"],
			"properties": {"index": {"type": "integer"}},
		},
	}


class AddPlanItemList(BaseModel):
	operations: List[AddPlanItem]

	model_schema: ClassVar[Dict] = {
		"type": "json_object",
		"schema": {
			"type": "object",
			"required": ["operations"],
			"properties": {
				"operations": {
					"type": "array",
					"items": AddPlanItem.model_schema["schema"],
				},
			},
		},
	}

	def apply(self, plan: "Plan") -> "Plan":
		"""Insert each plan item at the specified index.
		We sort by index ascending to keep relative order stable."""
		for op in sorted(self.operations, key=lambda o: o.index):
			plan.plan_items.insert(op.index, op.plan_item)
		return plan


class DeletePlanItemList(BaseModel):
	operations: List[DeletePlanItem]

	model_schema: ClassVar[Dict] = {
		"type": "json_object",
		"schema": {
			"type": "object",
			"required": ["operations"],
			"properties": {
				"operations": {
					"type": "array",
					"items": DeletePlanItem.model_schema["schema"],
				},
			},
		},
	}

	def apply(self, plan: "Plan") -> "Plan":
		"""Remove items, first mapping indices to _ids to avoid index-shift issues."""
		# First pass – map indices to IDs
		ids_to_remove = []
		for op in self.operations:
			if 0 <= op.index < len(plan.plan_items):
				ids_to_remove.append(plan.plan_items[op.index].id)
		# Second pass – reconstruct list without removed IDs
		plan.plan_items = [p for p in plan.plan_items if p.id not in ids_to_remove]
		return plan


PLAN_PREAMBLE = """
Your task is to fully explore and discover every single page of a web application
To accomplish this, you should try to trigger as many functionalities on the page as possible

Your goal is to discover the following elements on this page:
1. outgoing_links: links to other pages of the same web application
2. backend_calls: requests made to backend API services

You can find both by interacting with the webpage
Here are some strategies to guide your interaction:
- do not interact with elements that you suspect will trigger a navigation action off of the page
- elements on the page may be hidden, and to interact with them, you may have to perform some action such as expanding a submenu

Here are some strategies to help you generate a plan:
- each plan_item should only cover one action
- do not reference element indices in your plant_items

Here are some requirements around generating a plan-item:
- generate your plan as a plain sentence without any preceding notation
DO: "Do this ..."
NOT: "1) [*] Do this ..."
- if updating a plan, make sure the generated items are in the same order
- do not delete plan-items
- do not add instructions for going back to a previous navigation goal
- do not add plan-items that cover the same actions as pre-existing ones
"""

def generate_plan(llm: BaseChatModel, page_contents: str) -> Plan:
	PLAN_PROMPT = """
Formulate a plan for interacting with the visible elements on the page. You should output two parts:
1. First your observations about the page
2. Then a step by step plan to interact with the visible elements
	"""
	PLAN_PROMPT = PLAN_PREAMBLE + PLAN_PROMPT
	LLM_MSGS = [
		{"role": "system", "content": PLAN_PROMPT},
		{"role": "user", "content": page_contents},
	]

	full_logger.info(f"[PROMPT GENERATE PLAN]:\n{dump_llm_messages_pretty(LLM_MSGS)}")

	res = llm.invoke(LLM_MSGS, response_format=Plan.model_schema)
	res = json.loads(res.content)
	return Plan(**res)


@retry_sync(max_retries=3, exceptions=(Exception, ValueError), exc_class=EarlyShutdown)
def update_plan_with_messages(
	llm: BaseChatModel,
	messages: List[Dict[str, str]],
) -> AddPlanItemList:
	"""Call the LLM to get added plan items and return as an AddPlanItemList."""
	res = llm.invoke(messages, response_format=AddPlanItemList.model_schema)
	return AddPlanItemList(**json.loads(res.content))


@retry_sync(max_retries=3, exceptions=(Exception, ValueError), exc_class=EarlyShutdown)
def update_plan(
	llm: BaseChatModel,
	curr_page_contents: str,
	prev_page_contents: str,
	prev_plan: Plan,
	eval_prev_goal: str,
) -> Plan:
	UPDATE_PLAN_PROMPT = f"""
A plan was created to accomplish the goals above.
Here is the original plan:
{prev_plan}

Your goal is to update the plan if nessescary. This should happen for the following reasons:
1. the page has been dynamically updated, and a modification to the plan is required

Here are some requirements for updating plans:
- you can ONLY ADD plan-items
- you can NOT DELETE plan-items
- you can NOT MODIFY plan-items

Here is the previous page:
{prev_page_contents}

Here is the current page:
{curr_page_contents}

Here are the actions to affect this change:
{eval_prev_goal}

Some things to note:
- be wary of re-adding existing plan-items to the plan even if the last action failed

Return a list of plan-items to be added to the plan in json format
"""
	UPDATE_PLAN_PROMPT = PLAN_PREAMBLE + UPDATE_PLAN_PROMPT
	messages = [{"role": "user", "content": UPDATE_PLAN_PROMPT}]

	full_logger.info(f"[PROMPT UPDATE PLAN]: \n{dump_llm_messages_pretty(messages)}")

	plan_ops = llm.invoke(messages, response_format=AddPlanItemList.model_schema)
	plan_ops = AddPlanItemList(**json.loads(plan_ops.content))

	agent_logger.info(f"[PLAN UPDATE] Added {len(plan_ops.operations)} plan items")
	for op in plan_ops.operations:
		agent_logger.info(f"[PLAN UPDATE] AddPlanItem: {op.plan_item.plan}")

	plan_ops.apply(prev_plan)
	return prev_plan


class NewPageStatus(str, enum.Enum):
	SAME_PAGE = "same_page"
	NEW_PAGE = "new_page"
	UPDATED_PAGE = "updated_page"


class NavigationPage(BaseModel):
	page_type: NewPageStatus
	name: Optional[str] = ""
	model_schema: ClassVar[Dict] = {
		"type": "json_object",
		"schema": {
			"type": "object",
			"required": ["page_type"],
			"properties": {
				"page_type": {
					"type": "string",
					"enum": [status.value for status in NewPageStatus],
					"description": "The type of page transition that occurred",
				},
				"name": {
					"type": "string",
					"description": "Optional name for the updated page view",
				},
			},
		},
	}


def determine_new_page(
	llm: BaseChatModel,
	curr_page_contents: str,
	prev_page_contents: str,
	curr_url: str,
	prev_url: str,
	prev_goal: str,
	subpages: List[Tuple[str, str, str]],
	homepage_url: str,
	homepage_contents: str,
) -> NavigationPage:
	if curr_page_contents == prev_page_contents:
		return NavigationPage(page_type=NewPageStatus.SAME_PAGE, name="")

	# Check previously seen subpages
	highest_match = 0.0
	matched_subpage = None
	for url, page_contents, name in subpages:
		if curr_url != url:
			continue
		matcher = difflib.SequenceMatcher(None, curr_page_contents, page_contents)
		ratio = matcher.ratio()
		if ratio > highest_match:
			highest_match = ratio
			matched_subpage = name

	if highest_match > 0.9:
		full_logger.info(f"Found match for {curr_url} in existing subpage {matched_subpage}")
		return NavigationPage(page_type=NewPageStatus.UPDATED_PAGE, name=matched_subpage)

	NEW_PAGE_PROMPT = f"""
You are presented with the following views from a browser
Here is the CURR_PAGE:
URL: {curr_url}
{curr_page_contents}

Here is the PREV_PAGE:
URL: {prev_url}
{prev_page_contents}

Here is the HOMEPAGE:
URL: {homepage_url}
{homepage_contents}

Here is the action that was executed to get from the previous goal to here:
{prev_goal}

Given the different views, determine if the CURR_PAGE is a:

1. new_page: different from the HOMEPAGE
2. updated_page: same page of the application, but with an updated view (ie. submenu expansion, pop-up)
- if it is an updated_page, then also return the name of updated_page

Some things to keep in mind:
1. visible elements: the view presented only shows visible elements in the DOM; so elements that are on the same page might not be displayed because is_top_element == False or is_in_viewport == False

Which is why when considering whether the CURR_PAGE is a new_page or updated_page, make your decision by considering both the url and the DOM of the CURR_PAGE
Now make your choices
"""

	LLM_MSGS = [{"role": "user", "content": NEW_PAGE_PROMPT}]

	res = llm.invoke(LLM_MSGS, response_format=NavigationPage.model_schema)
	return NavigationPage(**json.loads(res.content))


class CompletePlan(BaseModel):
	completed: List[int]
	model_schema: ClassVar[Dict] = {
		"type": "json_object",
		"schema": {
			"type": "object",
			"required": ["completed"],
			"properties": {
				"completed": {
					"type": "array",
					"items": {
						"type": "integer",
						"description": "The indices of completed plan items",
					},
				},
			},
		},
	}


@retry_sync(max_retries=3, exceptions=(Exception), exc_class=EarlyShutdown)
def check_plan_completion(
	llm: BaseChatModel,
	plan: Plan,
	prev_page_contents: str,
	curr_page_contents: str,
	prev_goal: str,
) -> Plan:
	CHECK_PLAN = """
You are a web agent that is tasked with accomplishing some browser navigation goals

Here is the plan you are following:
{plan}

Here is the previous page:
{prev_page_contents}

Here is the current page:
{curr_page_contents}

Here is the action that you previously executed:
{prev_goal}

Give your output as a list of completed plan item indices
""".format(
		plan=plan,
		prev_page_contents=prev_page_contents,
		curr_page_contents=curr_page_contents,
		prev_goal=prev_goal,
	)

	LLM_MSGS = [{"role": "user", "content": CHECK_PLAN}]

	full_logger.info(f"[PROMPT CHECK PLAN]: \n{dump_llm_messages_pretty(LLM_MSGS)}")

	res = llm.invoke(LLM_MSGS, response_format=CompletePlan.model_schema)
	completed = CompletePlan(**json.loads(res.content))

	for idx in completed.completed:
		if 0 <= idx < len(plan.plan_items):
			plan.plan_items[idx].completed = True

	return plan


DEDUP_AFTER_STEPS = 5


@retry_sync(max_retries=3, exceptions=(Exception, ValueError), exc_class=EarlyShutdown)
def deduplicate_plan_with_messages(
	llm: BaseChatModel,
	messages: List[Dict[str, str]],
) -> DeletePlanItemList:
	res = llm.invoke(messages, response_format=DeletePlanItemList.model_schema)
	return DeletePlanItemList(**json.loads(res.content))


@retry_sync(max_retries=3, exceptions=(Exception, ValueError), exc_class=EarlyShutdown)
def deduplicate_plan(llm: BaseChatModel, plan: Plan) -> Plan:
	PROMPT = f"""
Here is a plan generated by a web agent:
{plan}

Your goal is to deduplicate the plan by removing any duplicate plan items.

Return a list of delete operations to remove duplicate plan items in json format.
Each delete operation should specify the index of the plan item to remove.
"""
	messages = [{"role": "user", "content": PROMPT}]

	agent_logger.info(f"Plan before: {len(plan.plan_items)}")
	full_logger.info(f"[PROMPT DEDUPLICATE PLAN]: \n{dump_llm_messages_pretty(messages)}")

	plan_ops = llm.invoke(messages, response_format=DeletePlanItemList.model_schema)
	plan_ops = DeletePlanItemList(**json.loads(plan_ops.content))

	agent_logger.info(f"[PLAN DEDUPLICATE] Removing {len(plan_ops.operations)} plan items")
	for op in plan_ops.operations:
		agent_logger.info(
			f"[PLAN DEDUPLICATE] DeletePlanItem: {plan.plan_items[op.index].plan}"
		)

	plan_ops.apply(plan)
	agent_logger.info(f"Plan after: {len(plan.plan_items)}")
	return plan
