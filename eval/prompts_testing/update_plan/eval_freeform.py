from src.llm_providers import cohere_client, deepseek_client, openai_client, cohere_client_thinking
from src.agent.discovery import update_plan_with_messages

PROMPT3 = [
  {
    "role": "user",
    "content": """
Your task is to fully explore and discover every single page of a web application
To accomplish this, you should try to trigger as many functionalities on the page as possible
Your goal is to discover the following elements on this page:
1. outgoing_links: links to other pages of the same web application
2. backend_calls: requests made to backend API services
You can find both by interacting with the webpage
Here are some strategies to guide your interaction:
- do not interact with elements that you suspect will trigger a navigation action off of the page
- elements on the page may be hidden, and to interact with them, you may have to perform some
action such as expanding a submenu
Here are some strategies to help you generate a plan:
- do not reference element indices in your plant_items
Here are some requirements around generating a plan-item:
- generate your plan as a plain sentence without any preceding notation
DO: "Do this ..."
NOT: "1) [*] Do this ..."
- if updating a plan, make sure the generated items are in the same order
- do not delete plan-items
- do not add instructions for going back to a previous navigation goal
- do not add plan-items that cover the same actions as pre-existing ones
A plan was created to accomplish the goals above.

Here is the original plan:
[ ] Product Interactions
      [ ] Juice Products
            [ ] Click the 'Apple Juice (1000ml)' image to trigger any associated functionality.
            [ ] Click the 'Add to Basket' button for Apple Juice to add it to the shopping cart.
            [ ] Click the 'Banana Juice (1000ml)' image to trigger any associated functionality.
            [ ] Click the 'Add to Basket' button for Banana Juice to add it to the shopping cart.
            [ ] Click the 'Carrot Juice (1000ml)' image to trigger any associated functionality.
            [ ] Click the 'Add to Basket' button for Carrot Juice to add it to the shopping cart.
            [ ] Click the 'Eggfruit Juice (500ml)' image to trigger any associated functionality.
            [ ] Click the 'Add to Basket' button for Eggfruit Juice to add it to the shopping cart.
      [ ] Other Products
            [ ] Click the 'Apple Pomace' image to trigger any associated functionality.
            [ ] Click the 'Add to Basket' button for Apple Pomace to add it to the shopping cart.
            [ ] Click the 'Best Juice Shop Salesman Artwork' image to trigger any associated functionality.
            [ ] Click the 'Add to Basket' button for the Artwork to add it to the shopping cart.
            [ ] Click the 'Fruit Press' image to trigger any associated functionality.
            [ ] Click the 'Green Smoothie' image to trigger any associated functionality.
            [ ] Click the 'Juice Shop "Permafrost" 2020 Edition' image to trigger any associated functionality.

Your goal is to update the plan if nessescary. This should happen for the following reasons:
1. the page has been dynamically updated, and a modification to the plan is required
Here are some requirements for updating plans:
- you can ONLY ADD plan-items
- you can NOT DELETE plan-items
- you can NOT MODIFY plan-items
Here is the previous page:
[0]<button aria-label='Open Sidenav'>menu />
[1]<button aria-label='Back to homepage' href='/search'>OWASP Juice Shop />
[2]<div  />
      [3]<input type='text' />
[4]<mat-icon role='img'>close />
[5]<button aria-label='Show/hide account menu' aria-expanded='false'>account_circle
Account />
[6]<button aria-label='Show the shopping cart' href='/basket'>shopping_cart
Your Basket
0 />
[7]<button aria-label='Language selection menu' aria-expanded='false'>language
EN />
Search Results -
Apple Juice
[8]<div >Apple Juice (1000ml)
1.99¤ />
      [9]<img role='button' alt='Apple Juice (1000ml)' />
[10]<button >Add to Basket />
Items per page:
[11]<div >12 />
      [12]<div  />
1 – 1 of 1
[13]<button type='button' aria-label='Previous page' />
[14]<button type='button' aria-label='Next page' />

Here is the current page (NEW_PAGE: NO, not seen before):
[0]<button aria-label='Open Sidenav'>menu />
[1]<button aria-label='Back to homepage' href='/search'>OWASP Juice Shop />
[2]<div  />
      [3]<input type='text' />
[4]<mat-icon role='img'>close />
[5]<button aria-label='Show/hide account menu' aria-expanded='false'>account_circle
Account />
[6]<button aria-label='Show the shopping cart' href='/basket'>shopping_cart
Your Basket
0 />
[7]<button aria-label='Language selection menu' aria-expanded='false'>language
EN />
All Products
[8]<div >Apple Juice (1000ml)
1.99¤ />
      [9]<img role='button' alt='Apple Juice (1000ml)' />
[10]<button >Add to Basket />
[11]<div >Apple Pomace
0.89¤ />
      [12]<img role='button' alt='Apple Pomace' />
[13]<button >Add to Basket />
[14]<div >Banana Juice (1000ml)
1.99¤ />
      [15]<img role='button' alt='Banana Juice (1000ml)' />
[16]<button >Add to Basket />
[17]<div >Best Juice Shop Salesman Artwork
5000¤ />
      [18]<img role='button' alt='Best Juice Shop Salesman Artwork' />
[19]<button >Add to Basket />
[20]<div >Carrot Juice (1000ml)
2.99¤ />
      [21]<img role='button' alt='Carrot Juice (1000ml)' />
[22]<button >Add to Basket />
[23]<div >Eggfruit Juice (500ml)
8.99¤ />
      [24]<img role='button' alt='Eggfruit Juice (500ml)' />
[25]<button >Add to Basket />
[26]<div >Fruit Press
89.99¤ />
      [27]<img role='button' alt='Fruit Press' />
[28]<div >Green Smoothie
1.99¤ />
      [29]<img role='button' alt='Green Smoothie' />
[30]<div >Juice Shop "Permafrost" 2020 Edition
9999.99¤ />
      [31]<img role='button' alt='Juice Shop "Permafrost" 2020 Edition' />

Here are the actions to affect this change:
Successful - The search functionality was triggered by pressing Enter, and the results page for
'Apple Juice' was displayed.

Some things to note:
- be wary of re-adding existing plan-items to the plan even if the last action failed

First generate an observation of the relevant section in the existing plan
In 
Then return a list of plan-items to be added to the plan
"""
  }
]

MODELS = [cohere_client]
# COHERE_ONLY = [cohere_client]
# MIXED = [cohere_client, deepseek_client]

for i in range(5):
    for client in MODELS:
        print(f"{i}. ### Using {client.__class__.__name__} ###")

        res = client.invoke(PROMPT3)
        print(res.content)
