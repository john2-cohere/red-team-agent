from johnllm import LLMModel, LMP
from langchain_core.messages import BaseMessage
from pydantic import BaseModel

MSGS = [
    {
        "role": "system",
        "content": "You are a good teacher"
    },
    {
        "role": "user",
        "content": "what is 1+!?"
    }
]

class Answer(BaseModel):
    answer: str

model = LLMModel()
res = model.invoke(MSGS, 
                   model_name="command-a-03-2025",
                   response_format=Answer)
print(res)
