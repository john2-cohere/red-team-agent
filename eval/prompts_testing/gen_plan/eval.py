from __future__ import annotations

import json
from typing import ClassVar, Dict, List, Optional
from pydantic import BaseModel

from src.llm_providers import cohere_client, deepseek_client
from src.agent.discovery import update_plan_with_messages


class PlanNode(BaseModel):
	"""
	A single node in a hierarchical plan.

	• The *plan* field acts as either a section title (for non-leaf nodes)
	  or the literal step to execute (for leaves).
	• *children* holds nested nodes; an empty list means “leaf”.
	• *completed* is only meaningful for leaves but is kept on every
	  node to avoid a union type and simplify JSON-Schema.
	"""

	plan: str
	completed: bool = False
	children: List["PlanNode"] = []

	model_schema: ClassVar[Dict] = {
		"type": "object",
		"required": ["plan", "children"],
		"properties": {
			"plan": {"type": "string", "description": "Title or actionable step"},
			"completed": {
				"type": "boolean",
				"default": False,
				"description": "Whether the step is completed (ignored for sections)",
			},
			"children": {
				"type": "array",
				"items": {"$ref": "#"},
				"description": "Sub-steps / subsections",
			},
		},
		"definitions": {},  # filled automatically by Pydantic
	}

	def is_leaf(self) -> bool:
		return len(self.children) == 0


class Plan(BaseModel):
	"""
	Encapsulates the entire hierarchy.  The *root* node itself is
	never rendered – everything lives under it.
	"""

	root: PlanNode

	def __str__(self) -> str:  # pretty print for humans
		return self._render(self.root, level=0)

	# ------------------------------------------------------------------
	# private helpers
	# ------------------------------------------------------------------
	def _render(self, node: PlanNode, level: int) -> str:
		prefix = "\t" * level
		out = ""
		if level > 0:  # skip printing the synthetic root
			checkbox = "[*]" if node.completed else "[ ]"
			out += f"{prefix}{checkbox} {node.plan}\n"
		for child in node.children:
			out += self._render(child, level + 1)
		return out


class AddPlanItem(BaseModel):
	"""
	Insert *plan_item* as a child of the node located at *parent_path*
	(list of indices from the root to that parent), *before* the element
	currently at *index* (append if index == len(children)).
	"""

	plan_item: PlanNode
	parent_path: List[int] = []  # [] means “root”
	index: int = 0

	model_schema: ClassVar[Dict] = {
		"type": "object",
		"required": ["plan_item", "parent_path", "index"],
		"properties": {
			"plan_item": PlanNode.model_schema,
			"parent_path": {
				"type": "array",
				"items": {"type": "integer"},
				"description": "Path of indices from root to parent",
			},
			"index": {
				"type": "integer",
				"description": "Insertion position inside the parent’s children",
			},
		},
	}

	def op(self, plan: Plan) -> Plan:
		parent = self._locate(plan.root, self.parent_path)
		if self.index < 0 or self.index > len(parent.children):
			raise IndexError("index out of bounds for parent.children")
		parent.children.insert(self.index, self.plan_item)
		return plan

	# ------------------------------------------------------------------
	# private helpers
	# ------------------------------------------------------------------
	@staticmethod
	def _locate(node: PlanNode, path: List[int]) -> PlanNode:
		for i in path:
			if i < 0 or i >= len(node.children):
				raise IndexError("parent_path is invalid")
			node = node.children[i]
		return node


class Operations(BaseModel):
	operations: List[AddPlanItem]

	model_schema: ClassVar[Dict] = {
		"type": "object",
		"required": ["operations"],
		"properties": {
			"operations": {
				"type": "array",
				"items": AddPlanItem.model_schema,
			}
		},
	}

	def apply(self, plan: Plan) -> Plan:
		for op in self.operations:
			op.op(plan)
		return plan


# PROMPT = [
#   {
#     "role": "user",
#     "content": f"""
# Your task is to fully explore and discover every single page of a web application
# To accomplish this, you should try to trigger as many functionalities on the page as possible
# Your goal is to discover the following elements on this page:
# 1. outgoing_links: links to other pages of the same web application
# 2. backend_calls: requests made to backend API services
# You can find both by interacting with the webpage
# Here are some strategies to guide your interaction:
# - do not interact with elements that you suspect will trigger a navigation action off of the page
# - elements on the page may be hidden, and to interact with them, you may have to perform some
# action such as expanding a submenu

# When generating your plan, you should first:
# 1. Decompose the page into different sections
# 2. Use this hierarichal structure to group your plans

# Here are some strategies to help you generate a plan:
# - each plan_item should only cover one action
# - do not reference element indices in your plant_items

# Here are some requirements around generating a plan-item:
# - generate your plan as a plain sentence without any preceding notation
# DO: "Do this ..."
# NOT: "1) [*] Do this ..."
# - if updating a plan, make sure the generated items are in the same order
# - do not delete plan-items
# - do not add instructions for going back to a previous navigation goal
# - do not add plan-items that cover the same actions as pre-existing ones

# Formulate a plan for interacting with the visible elements on the page. You should output two
# parts:
# 1. First your observations about the page
# 2. Then a step by step plan to interact with the visible elements

# [0]<button aria-label='Open Sidenav'>menu />
# [1]<button aria-label='Back to homepage' href='/search'>OWASP Juice Shop />
# [2]<mat-icon role='img'>search />
# [3]<button aria-label='Show/hide account menu' aria-expanded='false'>account_circle
# Account />
# [4]<button aria-label='Show the shopping cart' href='/basket'>shopping_cart
# Your Basket
# 0 />
# [5]<button aria-label='Language selection menu' aria-expanded='false'>language
# EN />
# All Products
# [6]<div >Apple Juice (1000ml)
# 1.99¤ />
#     [7]<img role='button' alt='Apple Juice (1000ml)' />
# [8]<button >Add to Basket />
# [9]<div >Apple Pomace
# 0.89¤ />
#     [10]<img role='button' alt='Apple Pomace' />
# [11]<button >Add to Basket />
# [12]<div >Banana Juice (1000ml)
# 1.99¤ />
#     [13]<img role='button' alt='Banana Juice (1000ml)' />
# [14]<button >Add to Basket />
# [15]<div >Best Juice Shop Salesman Artwork
# 5000¤ />
#     [16]<img role='button' alt='Best Juice Shop Salesman Artwork' />
# [17]<button >Add to Basket />
# [18]<div >Carrot Juice (1000ml)
# 2.99¤ />
#     [19]<img role='button' alt='Carrot Juice (1000ml)' />
# [20]<button >Add to Basket />
# [21]<div >Eggfruit Juice (500ml)
# 8.99¤ />
#     [22]<img role='button' alt='Eggfruit Juice (500ml)' />
# [23]<button >Add to Basket />
# [24]<div >Fruit Press
# 89.99¤ />
#     [25]<img role='button' alt='Fruit Press' />
# [26]<div >Green Smoothie
# 1.99¤ />
#     [27]<img role='button' alt='Green Smoothie' />
# [28]<div >Juice Shop "Permafrost" 2020 Edition
# 9999.99¤ />
#     [29]<img role='button' alt='Juice Shop "Permafrost" 2020 Edition' />

# Generate your plans in hierarchal form by using "--" * DEPTH ">" to indicate depth. Here is an example:
# HOMEPAGE:
# > MORTGAGE_QUOTES
# --> Click on quote1
# --> Click on quote2
# --> Click on quote3
# > HEADER
# --> PROFILE
# ----> Click on profile
# --> SEARCH
# ----> Click on search

# As a genius expert, your task is to understand the content and provide
# the parsed objects in json that match the following json_schema:\n

# {json.dumps(PlanNode.model_json_schema(), indent=2, ensure_ascii=False)}

# Make sure to return an instance of the JSON, not the schema itself
#     """
#   }
# ]

# res = cohere_client.invoke(PROMPT)
# json_str = res.content.split("```json")[1].split("```")[0]
# plan = Plan(root=PlanNode(**json.loads(json_str)))
# print(plan)


plan = Plan(root=PlanNode(
    plan="Juice Shop Navigation and Interaction Plan",
    completed=False,
    children=[
        PlanNode(
            plan="Navigation and Menu Interactions",
            completed=False,
            children=[
                PlanNode(plan="Click the 'Open Sidenav' button to expand the side navigation menu.", completed=False, children=[]),
                PlanNode(plan="Click the 'Back to homepage' button to navigate to the search page.", completed=False, children=[]),
                PlanNode(plan="Click the 'Show/hide account menu' button to expand the account menu.", completed=False, children=[]),
                PlanNode(plan="Click the 'Show the shopping cart' button to navigate to the basket page.", completed=False, children=[]),
                PlanNode(plan="Click the 'Language selection menu' button to expand the language selection menu.", completed=False, children=[])
            ]
        ),
        PlanNode(
            plan="Search Functionality",
            completed=False,
            children=[
                PlanNode(plan="Enter a search term into the search input field to trigger search functionality.", completed=False, children=[]),
                PlanNode(plan="Click the 'search' icon to trigger a search functionality.", completed=False, children=[])
            ]
        ),
        PlanNode(
            plan="Product Interactions",
            completed=False,
            children=[
                PlanNode(
                    plan="Juice Products",
                    completed=False,
                    children=[
                        PlanNode(plan="Click the 'Apple Juice (1000ml)' image to trigger any associated functionality.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Add to Basket' button for Apple Juice to add it to the shopping cart.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Banana Juice (1000ml)' image to trigger any associated functionality.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Add to Basket' button for Banana Juice to add it to the shopping cart.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Carrot Juice (1000ml)' image to trigger any associated functionality.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Add to Basket' button for Carrot Juice to add it to the shopping cart.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Eggfruit Juice (500ml)' image to trigger any associated functionality.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Add to Basket' button for Eggfruit Juice to add it to the shopping cart.", completed=False, children=[])
                    ]
                ),
                PlanNode(
                    plan="Other Products",
                    completed=False,
                    children=[
                        PlanNode(plan="Click the 'Apple Pomace' image to trigger any associated functionality.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Add to Basket' button for Apple Pomace to add it to the shopping cart.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Best Juice Shop Salesman Artwork' image to trigger any associated functionality.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Add to Basket' button for the Artwork to add it to the shopping cart.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Fruit Press' image to trigger any associated functionality.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Green Smoothie' image to trigger any associated functionality.", completed=False, children=[]),
                        PlanNode(plan="Click the 'Juice Shop \"Permafrost\" 2020 Edition' image to trigger any associated functionality.", completed=False, children=[])
                    ]
                )
            ]
        ),
        PlanNode(
            plan="Page Navigation Links",
            completed=False,
            children=[
                PlanNode(plan="Click the 'Go to contact us page' link to navigate to the contact page.", completed=False, children=[]),
                PlanNode(plan="Click the 'Go to complain page' link to navigate to the complain page.", completed=False, children=[]),
                PlanNode(plan="Click the 'Go to about us page' link to navigate to the about us page.", completed=False, children=[]),
                PlanNode(plan="Click the 'Go to chatbot page' link to navigate to the chatbot page.", completed=False, children=[]),
                PlanNode(plan="Click the 'Go to photo wall' link to navigate to the photo wall page.", completed=False, children=[]),
                PlanNode(plan="Click the 'Go to deluxe membership page' link to navigate to the deluxe membership page.", completed=False, children=[])
            ]
        ),
        PlanNode(
            plan="Special Features",
            completed=False,
            children=[
                PlanNode(plan="Click the 'Launch beginners tutorial' link to trigger the tutorial functionality.", completed=False, children=[]),
                PlanNode(plan="Click the 'Go to OWASP Juice Shop GitHub page' link to navigate to the GitHub page.", completed=False, children=[])
            ]
        )
    ]
))


print(plan)