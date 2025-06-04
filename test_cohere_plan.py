from johnllm import LLMModel, LMP
from typing import List
from langchain_core.messages import BaseMessage
from cohere import ClientV2, Client

from langchain_cohere import ChatCohere
from data import JUICE_SHOP_HOMEPAGE_NO_POPUP

import json
from pydantic import BaseModel
import instructor


class PlanItem(BaseModel):
    plan: str
    completed: bool = False

class Plan(BaseModel):
    plan_items: List[PlanItem]
    
PLAN_PAGE_NAVIGATION = [
    {
        "role": "system",
        "content" :
"""
Your task is to fully explore and discover every single page of a web application
To accomplish this, you should try to trigger as many functionalities on the page as possible

Your goal is to discover the following elements on this page:
1. outgoing_links: links to other pages of the same web application
2. backend_calls: requests made to backend API services

You can find both by interacting with the webpage
Here are some strategies to guide your interaction:
- do not interact with elements that you suspect will trigger a navigation action off of the page
- elements on the page may be hidden, and to interact with them, you may have to perform some action such as expanding a submenu  

Formulate a plan for interacting with the visible elements on the page. You should output two parts:
1. First your observations about the page
2. Then a step by step plan to interact with the visible elements
"""
    },
    {
        "role": "user",
        "content": JUICE_SHOP_HOMEPAGE_NO_POPUP
    }
]

# client = ClientV2()
# res = client.chat(messages=PLAN_PAGE_NAVIGATION, model="command-a-03-2025")

# client = ChatCohere(model="command-a-03-2025")
client = ChatCohere(
        model="north-reasoning-alpha", #"command-r7b-12-2024" #"command-r-plus-08-2024",
        model_kwargs={
            'thinking': {
                'type': 'enabled'
            }
        }
)
res = client.invoke(PLAN_PAGE_NAVIGATION, response_format = {
    "type": "json_object",
    "schema": {
        "type": "object",
        "required": ["plan_items"],
        "properties": {
            "plan_items": {
                "type": "array",
                "items": {
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
            }
        }
    }
})
for plan in Plan(**json.loads(res.content)).plan_items:
    print(plan)

# client = instructor.from_cohere(
#     Client(),
#     model="command-a-03-2025",
# )
# res = client.messages.create(messages=PLAN_PAGE_NAVIGATION, response_model=Plan)
# for plan in res.plan_items:
#     print(plan)