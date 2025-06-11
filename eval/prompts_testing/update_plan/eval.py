from ..llm import cohere_client, deepseek_client

from src.agent.discovery import update_plan_with_messages

PROMPT = [
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
- each plan_item should only cover one action
- do not reference element indices in your plant_items

<requirements>
Here are some requirements around generating a plan-item:
- generate your plan as a plain sentence without any preceding notation
DO: "Do this ..."
NOT: "1) [*] Do this ..."
- if updating a plan, make sure the generated items are in the same order
- do not delete plan-items
- do not add instructions for going back to a previous navigation goal
</requirements>

<plan_items>
A plan was created to accomplish the goals above.
Here is the original plan:
0) [*]   Click the 'Open Sidenav' button to explore any hidden navigation options.
1) [ ]   Click the 'Back to homepage' button to ensure it navigates to the search page.
2) [ ]   Interact with the 'search' icon to trigger any search functionality.
3) [ ]   Click the 'Show/hide account menu' button to expand the account menu and explore its
options.
4) [ ]   Click the 'Show the shopping cart' button to navigate to the basket page.
5) [ ]   Click the 'Language selection menu' button to expand the language options.
6) [ ]   Click on the 'Apple Juice (1000ml)' image to trigger any product detail view or action.
7) [ ]   Click the 'Add to Basket' button for Apple Juice to trigger a backend call for adding the
product to the cart.
8) [ ]   Click on the 'Apple Pomace' image to trigger any product detail view or action.
9) [ ]   Click the 'Add to Basket' button for Apple Pomace to trigger a backend call for adding
the product to the cart.
10) [ ]   Click on the 'Banana Juice (1000ml)' image to trigger any product detail view or action.
11) [ ]   Click the 'Add to Basket' button for Banana Juice to trigger a backend call for adding
the product to the cart.
12) [ ]   Click on the 'Best Juice Shop Salesman Artwork' image to trigger any product detail view
or action.
13) [ ]   Click the 'Add to Basket' button for the Artwork to trigger a backend call for adding
the product to the cart.
14) [ ]   Click on the 'Carrot Juice (1000ml)' image to trigger any product detail view or action.
15) [ ]   Click the 'Add to Basket' button for Carrot Juice to trigger a backend call for adding
the product to the cart.
16) [ ]   Click on the 'Eggfruit Juice (500ml)' image to trigger any product detail view or
action.
17) [ ]   Click the 'Add to Basket' button for Eggfruit Juice to trigger a backend call for adding
the product to the cart.
18) [ ]   Click on the 'Fruit Press' image to trigger any product detail view or action.
19) [ ]   Click on the 'Green Smoothie' image to trigger any product detail view or action.
20) [ ]   Click on the 'Juice Shop "Permafrost" 2020 Edition' image to trigger any product detail
view or action.
</plan_items>

Your goal is to update the plan if nessescary. This should happen for the following reasons:
1. the page has been dynamically updated, and a modification to the plan is required
Here are some requirements for updating plans:
- you can ONLY ADD plan-items
- you can NOT DELETE plan-items
- you can NOT MODIFY plan-items

Here is the previous page:
[0]<button aria-label='Open Sidenav'>menu />
[1]<button aria-label='Back to homepage' href='/search'>OWASP Juice Shop />
[2]<mat-icon role='img'>search />
[3]<button aria-label='Show/hide account menu' aria-expanded='false'>account_circle
Account />
[4]<button aria-label='Show the shopping cart' href='/basket'>shopping_cart
Your Basket
0 />
[5]<button aria-label='Language selection menu' aria-expanded='false'>language
EN />
All Products
[6]<div >Apple Juice (1000ml)
1.99¤ />
    [7]<img role='button' alt='Apple Juice (1000ml)' />
[8]<button >Add to Basket />
[9]<div >Apple Pomace
0.89¤ />
    [10]<img role='button' alt='Apple Pomace' />
[11]<button >Add to Basket />
[12]<div >Banana Juice (1000ml)
1.99¤ />
    [13]<img role='button' alt='Banana Juice (1000ml)' />
[14]<button >Add to Basket />
[15]<div >Best Juice Shop Salesman Artwork
5000¤ />
    [16]<img role='button' alt='Best Juice Shop Salesman Artwork' />
[17]<button >Add to Basket />
[18]<div >Carrot Juice (1000ml)
2.99¤ />
    [19]<img role='button' alt='Carrot Juice (1000ml)' />
[20]<button >Add to Basket />
[21]<div >Eggfruit Juice (500ml)
8.99¤ />
    [22]<img role='button' alt='Eggfruit Juice (500ml)' />
[23]<button >Add to Basket />
[24]<div >Fruit Press
89.99¤ />
    [25]<img role='button' alt='Fruit Press' />
[26]<div >Green Smoothie
1.99¤ />
    [27]<img role='button' alt='Green Smoothie' />
[28]<div >Juice Shop "Permafrost" 2020 Edition
9999.99¤ />
    [29]<img role='button' alt='Juice Shop "Permafrost" 2020 Edition' />
Here is the current page:
[0]<div  />
[1]<mat-sidenav >OWASP Juice Shop
Account
account_circle
john@juice-sh.op
check_circle_outline
Orders & Payment
expand_more
security
Privacy & Security
expand_more
power_settings_new
Logout
Contact
Company
OWASP Juice Shop
v17.3.0 />
    [2]<a aria-label='Go to contact us page' href='/contact' />
            [3]<span  />
                    [4]<span >feedback
Customer Feedback />
    [5]<a aria-label='Go to complain page' href='/complain' />
            [6]<span  />
                    [7]<span >sentiment_dissatisfied
Complaint />
    [8]<a aria-label='Go to chatbot page' href='/chatbot' />
            [9]<span  />
                    [10]<span >chat
Support Chat />
    [11]<a aria-label='Go to about us page' href='/about' />
            [12]<span  />
                    [13]<span >business_center
About Us />
    [14]<a aria-label='Go to photo wall' href='/photo-wall' />
            [15]<span  />
                    [16]<span >camera
Photo Wall />
    [17]<a aria-label='Go to deluxe membership page' href='/deluxe-membership' />
            [18]<span  />
                    [19]<span >card_membership
Deluxe Membership />
    [20]<a aria-label='Launch beginners tutorial' />
            [21]<span  />
                    [22]<span >school
Help getting started />
    [23]<a aria-label='Go to OWASP Juice Shop GitHub page' />
            [24]<span  />
                    [25]<span >GitHub />
Here are the actions to affect this change:
Successfully clicked the 'Open Sidenav' button

Return the newly updated plan
    """
  }
]

for i in range(5):
    for client in [cohere_client, deepseek_client]:
        print(f"{i}. ### Using {client.__class__.__name__} ###")

        plan_items = update_plan_with_messages(cohere_client, PROMPT)
        for item in plan_items:
            print(item.plan_item.plan)