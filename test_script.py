from langsmith.wrappers import wrap_openai

from cohere import ClientV2

client = wrap_openai(ClientV2())

MSGS = [
    {
        "role": "user",
        "content": "whats the weatehr?"
    }
]

res = client.chat(messages=MSGS, model="command-a-03-2025")
print(res.message.content[0].text)