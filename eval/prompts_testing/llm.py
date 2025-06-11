from langchain_cohere import ChatCohere
from langchain_deepseek import ChatDeepSeek

import os

cohere_client = ChatCohere(
    model="command-a-03-2025",
    cohere_api_key=os.getenv("COHERE_API_KEY"),
)

deepseek_client = ChatDeepSeek(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

deepseek_client_reasoner = ChatDeepSeek(
    model="deepseek-reasoner",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

cohere_client_thinking = ChatCohere(
    model="north-reasoning-alpha", #"command-r7b-12-2024" #"command-r-plus-08-2024",
    model_kwargs={
        'thinking': {
            'type': 'enabled'
        }
    }
)