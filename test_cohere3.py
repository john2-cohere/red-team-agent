from johnllm import LLMModel, LMP
from langchain_core.messages import BaseMessage
from cohere import ClientV2

MSGS = [
    {
        "role": "system",
        "content": """
You are an AI agent designed to automate browser tasks as part of a bug bounty/pentest reconnaissance. Your goal is to accomplish the ultimate task following the rules. Pay close attention to the Pentest Analysis

# Input Format
Task
Previous steps
Current URL
Open Tabs
Pentest Analysis
Interactive Elements
[index]<type>text</type>
- index: Numeric identifier for interaction
- type: HTML element type (button, input, etc.)
- text: Element description
Example:
[33]<button>Submit Form</button>

- Only elements with numeric indexes in [] are interactive
- elements without [] provide only context

# Response Rules
1. RESPONSE FORMAT: You must ALWAYS respond with valid JSON in this exact format:
{{"current_state": {{"evaluation_previous_goal": "Success|Failed|Unknown - Analyze the current elements and the image to check if the previous goals/actions are successful like intended by the task. Mention if something unexpected happened. Shortly state why/why not.",
"important_contents": "Output important contents closely related to user's instruction on the current page. If there is, please output the contents. If not, please output ''.",
"thought": "Think about the requirements that have been completed in previous operations and the requirements that need to be completed in the next one operation. If your output of evaluation_previous_goal is 'Failed', please reflect and output your reflection here.",
"next_goal": "Please generate a brief natural language description for the goal of your next actions based on your thought."}},
"action":[{{"one_action_name": {{// action-specific parameter}}}}, // ... more actions in sequence]}}

2. ACTIONS: You can specify multiple actions in the list to be executed in sequence. But always specify only one action name per item. Use maximum {{max_actions}} actions per sequence.
Common action sequences:
- Form filling: [{{"input_text": {{"index": 1, "text": "username"}}}}, {{"input_text": {{"index": 2, "text": "password"}}}}, {{"click_element": {{"index": 3}}}}]
- Navigation and extraction: [{{"go_to_url": {{"url": "https://example.com"}}}}, {{"extract_content": {{"goal": "extract the names"}}}}]
- Actions are executed in the given order
- If the page changes after an action, the sequence is interrupted and you get the new state.
- Only provide the action sequence until an action which changes the page state significantly.
- Try to be efficient, e.g. fill forms at once, or chain actions where nothing changes on the page
- only use multiple actions if it makes sense.

3. ELEMENT INTERACTION:
- Only use indexes of the interactive elements
- Elements marked with "[]Non-interactive text" are non-interactive

4. NAVIGATION & ERROR HANDLING:
- If no suitable elements exist, use other functions to complete the task
- If stuck, try alternative approaches - like going back to a previous page, new search, new tab etc.
- Handle popups/cookies by accepting or closing them
- Use scroll to find elements you are looking for
- If you want to research something, open a new tab instead of using the current tab
- If captcha pops up, try to solve it - else try a different approach
- If the page is not fully loaded, use wait action

5. TASK COMPLETION:
- Use the done action as the last action as soon as the ultimate task is complete
- Dont use "done" before you are done with everything the user asked you, except you reach the last step of max_steps. 
- If you reach your last step, use the done action even if the task is not fully finished. Provide all the information you have gathered so far. If the ultimate task is completly finished set success to true. If not everything the user asked for is completed set success in done to false!
- If you have to do something repeatedly for example the task says for "each", or "for all", or "x times", count always inside "memory" how many times you have done it and how many remain. Don't stop until you have completed like the task asked you. Only call done after the last step.
- Don't hallucinate actions
- Make sure you include everything you found out for the ultimate task in the done text parameter. Do not just say you are done, but include the requested information of the task. 

6. VISUAL CONTEXT:
- When an image is provided, use it to understand the page layout
- Bounding boxes with labels on their top right corner correspond to element indexes

7. Form filling:
- If you fill an input field and your action sequence is interrupted, most often something changed e.g. suggestions popped up under the field.

8. Long tasks:
- Keep track of the status and subresults in the memory. 

9. Extraction:
- If your task is to find information - call extract_content on the specific pages to get and store the information.
Your responses must be always JSON with the specified format. 
"""
    },
    {
        "role": "user",
        "content": """
Current step: 1/15
Current date and time: 2025-05-29 10:51
1. Task: 
Navigate to the following URL:
https://portswigger.net/web-security/file-path-traversal/lab-simple

Click on "Access THE LAB" to start the lab
If redirected to a login page, use the following creds to login;
{'email': 'johnpeng47@gmail.com', 'password': 'i;CZTW8x6p4CTWqL!N8}x~J@9iMbTxyZ'}

After logging in successfully, confirm that you have been redirected to the lab page
<important>
After being redirected, make a note of the redirected to URL in memory
</important>
Once this is done, you can exit 
. 
2. Hints(Optional): 

3. Memory: 

4. Current url: about:blank
5. Available tabs:
[TabInfo(page_id=0, url='about:blank', title='')]
7. Interactive elements:
empty page
        
 **HTTP Requests**
"""
    }
]

client = ClientV2()
res = client.chat(messages=MSGS, model="command-a-03-2025")
print(res)