from src.llm_providers import cohere_client, deepseek_client, openai_client
from src.agent.discovery import update_plan_with_messages

import tiktoken

def num_tokens_from_string(messages: list[dict], encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in the content field of a list of messages."""
    encoding = tiktoken.get_encoding(encoding_name)
    total_tokens = 0
    for message in messages:
        content = message.get("content", "")
        total_tokens += len(encoding.encode(content, disallowed_special=()))
    return total_tokens

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

PROMPT2 = [
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
0) [*]   Do this Click the 'Open Sidenav' button to expand the side navigation menu.
1) [*]   Do this Click the 'Back to homepage' button to navigate to the search page.
2) [ ]   Do this Click the 'search' icon to trigger a search functionality.
3) [ ]   Do this Click the 'Show/hide account menu' button to expand the account menu.
4) [ ]   Do this Click the 'Show the shopping cart' button to navigate to the basket page.
5) [ ]   Do this Click the 'Language selection menu' button to expand the language selection menu.
6) [ ]   Do this Click the 'Apple Juice (1000ml)' image to interact with the product.
7) [ ]   Do this Click the 'Add to Basket' button for Apple Juice to add it to the cart.
8) [ ]   Do this Click the 'Apple Pomace' image to interact with the product.
9) [ ]   Do this Click the 'Add to Basket' button for Apple Pomace to add it to the cart.
10) [ ]   Do this Click the 'Banana Juice (1000ml)' image to interact with the product.
11) [ ]   Do this Click the 'Add to Basket' button for Banana Juice to add it to the cart.
12) [ ]   Do this Click the 'Best Juice Shop Salesman Artwork' image to interact with the product.
13) [ ]   Do this Click the 'Add to Basket' button for the Artwork to add it to the cart.
14) [ ]   Do this Click the 'Carrot Juice (1000ml)' image to interact with the product.
15) [ ]   Do this Click the 'Add to Basket' button for Carrot Juice to add it to the cart.
16) [ ]   Do this Click the 'Eggfruit Juice (500ml)' image to interact with the product.
17) [ ]   Do this Click the 'Add to Basket' button for Eggfruit Juice to add it to the cart.
18) [ ]   Do this Click the 'Fruit Press' image to interact with the product.
19) [ ]   Do this Click the 'Green Smoothie' image to interact with the product.
20) [ ]   Do this Click the 'Juice Shop "Permafrost" 2020 Edition' image to interact with the
product.
21) [*]   Do this Click the 'Go to contact us page' link to navigate to the contact page.
22) [*]   Do this Click the 'Go to complain page' link to navigate to the complain page.
23) [*]   Do this Click the 'Go to chatbot page' link to navigate to the chatbot page.
24) [*]   Do this Click the 'Go to about us page' link to navigate to the about us page.
25) [*]   Do this Click the 'Go to photo wall' link to navigate to the photo wall page.
26) [*]   Do this Click the 'Go to deluxe membership page' link to navigate to the deluxe
membership page.
27) [*]   Do this Click the 'Launch beginners tutorial' link to start the tutorial.
28) [*]   Do this Click the 'Go to OWASP Juice Shop GitHub page' link to navigate to the GitHub
page.
29) [*]   Do this Click the 'Score Board' link to navigate to the score board page.
30) [*]   Click the 'Open Sidenav' button to expand the side navigation menu.
31) [*]   Click the 'Back to homepage' button to navigate to the search page.
32) [ ]   Do this Click the 'search' icon to trigger a search functionality.
33) [ ]   Do this Click the 'Show/hide account menu' button to expand the account menu.
34) [ ]   Do this Click the 'Show the shopping cart' button to navigate to the basket page.
35) [ ]   Do this Click the 'Language selection menu' button to expand the language selection
menu.
36) [ ]   Do this Click the 'Apple Juice (1000ml)' image to interact with the product.
37) [ ]   Do this Click the 'Add to Basket' button for Apple Juice to add it to the cart.
38) [ ]   Do this Click the 'Apple Pomace' image to interact with the product.
39) [ ]   Do this Click the 'Add to Basket' button for Apple Pomace to add it to the cart.
40) [ ]   Do this Click the 'Banana Juice (1000ml)' image to interact with the product.
41) [ ]   Do this Click the 'Add to Basket' button for Banana Juice to add it to the cart.
42) [ ]   Do this Click the 'Best Juice Shop Salesman Artwork' image to interact with the product.
43) [ ]   Do this Click the 'Add to Basket' button for the Artwork to add it to the cart.
44) [ ]   Do this Click the 'Carrot Juice (1000ml)' image to interact with the product.
45) [ ]   Do this Click the 'Add to Basket' button for Carrot Juice to add it to the cart.
46) [ ]   Do this Click the 'Eggfruit Juice (500ml)' image to interact with the product.
47) [ ]   Do this Click the 'Add to Basket' button for Eggfruit Juice to add it to the cart.
48) [ ]   Do this Click the 'Fruit Press' image to interact with the product.
49) [ ]   Do this Click the 'Green Smoothie' image to interact with the product.
50) [ ]   Do this Click the 'Juice Shop "Permafrost" 2020 Edition' image to interact with the
product.
51) [ ]   Do this Click the 'Orders & Payment' link to navigate to the orders and payment page.
52) [ ]   Do this Click the 'Privacy & Security' link to navigate to the privacy and security
page.
53) [ ]   Do this Click the 'Logout' button to log out of the account.
54) [ ]   Do this Click the 'Orders & Payment' link to navigate to the orders and payment page.
55) [ ]   Do this Click the 'Privacy & Security' link to navigate to the privacy and security
page.
56) [ ]   Do this Click the 'Logout' button to log out of the account.
57) [ ]   Do this Click the 'Orders & Payment' link to navigate to the orders and payment page.
58) [ ]   Do this Click the 'Privacy & Security' link to navigate to the privacy and security
page.
59) [ ]   Do this Click the 'Logout' button to log out of the account.
60) [ ]   Do this Click the 'Orders & Payment' link to navigate to the orders and payment page.
61) [ ]   Do this Click the 'Privacy & Security' link to navigate to the privacy and security
page.
62) [ ]   Do this Click the 'Logout' button to log out of the account.
63) [*]   Do this Click the 'Open Sidenav' button to expand the side navigation menu.
64) [*]   Do this Click the 'Back to homepage' button to navigate to the search page.
65) [ ]   Do this Click the 'search' icon to trigger a search functionality.
66) [ ]   Do this Click the 'Show/hide account menu' button to expand the account menu.
67) [ ]   Do this Click the 'Show the shopping cart' button to navigate to the basket page.
68) [ ]   Do this Click the 'Language selection menu' button to expand the language selection
menu.
69) [ ]   Do this Click the 'Apple Juice (1000ml)' image to interact with the product.
70) [ ]   Do this Click the 'Add to Basket' button for Apple Juice to add it to the cart.
71) [ ]   Do this Click the 'Apple Pomace' image to interact with the product.
72) [ ]   Do this Click the 'Add to Basket' button for Apple Pomace to add it to the cart.
73) [ ]   Do this Click the 'Banana Juice (1000ml)' image to interact with the product.
74) [ ]   Do this Click the 'Add to Basket' button for Banana Juice to add it to the cart.
75) [ ]   Do this Click the 'Best Juice Shop Salesman Artwork' image to interact with the product.
76) [ ]   Do this Click the 'Add to Basket' button for the Artwork to add it to the cart.
77) [ ]   Do this Click the 'Carrot Juice (1000ml)' image to interact with the product.
78) [ ]   Do this Click the 'Add to Basket' button for Carrot Juice to add it to the cart.
79) [ ]   Do this Click the 'Eggfruit Juice (500ml)' image to interact with the product.
80) [ ]   Do this Click the 'Add to Basket' button for Eggfruit Juice to add it to the cart.
81) [ ]   Do this Click the 'Fruit Press' image to interact with the product.
82) [ ]   Do this Click the 'Green Smoothie' image to interact with the product.
83) [ ]   Do this Click the 'Juice Shop "Permafrost" 2020 Edition' image to interact with the
product.
84) [ ]   Do this Click the 'Go to contact us page' link to navigate to the contact page.
85) [ ]   Do this Click the 'Go to complain page' link to navigate to the complain page.
86) [ ]   Do this Click the 'Go to chatbot page' link to navigate to the chatbot page.
87) [ ]   Do this Click the 'Go to about us page' link to navigate to the about us page.
88) [ ]   Do this Click the 'Go to photo wall' link to navigate to the photo wall page.
89) [ ]   Do this Click the 'Go to deluxe membership page' link to navigate to the deluxe
membership page.
90) [ ]   Do this Click the 'Launch beginners tutorial' link to start the tutorial.
91) [ ]   Do this Click the 'Go to OWASP Juice Shop GitHub page' link to navigate to the GitHub
page.
92) [*]   Click the 'Open Sidenav' button to expand the side navigation menu.
93) [ ]   Click the 'Back to homepage' button to navigate to the search page.
94) [ ]   Click the 'search' icon to trigger a search functionality.
95) [ ]   Click the 'Show/hide account menu' button to expand the account menu.
96) [ ]   Click the 'Show the shopping cart' button to navigate to the basket page.
97) [ ]   Click the 'Language selection menu' button to expand the language selection menu.
98) [ ]   Click the 'Apple Juice (1000ml)' image to interact with the product.
99) [ ]   Click the 'Add to Basket' button for Apple Juice to add it to the cart.
100) [ ]   Click the 'Apple Pomace' image to interact with the product.
101) [ ]   Click the 'Add to Basket' button for Apple Pomace to add it to the cart.
102) [ ]   Click the 'Banana Juice (1000ml)' image to interact with the product.
103) [ ]   Click the 'Add to Basket' button for Banana Juice to add it to the cart.
104) [ ]   Click the 'Best Juice Shop Salesman Artwork' image to interact with the product.
105) [ ]   Click the 'Add to Basket' button for the Artwork to add it to the cart.
106) [ ]   Click the 'Carrot Juice (1000ml)' image to interact with the product.
107) [ ]   Do this Click the 'Contact' link to navigate to the contact page.
108) [ ]   Do this Click the 'Company' link to navigate to the company page.
109) [ ]   Do this Click the 'OWASP Juice Shop' link to navigate to the OWASP Juice Shop page.
110) [ ]   Do this Click the 'v17.3.0' link to navigate to the version page.
111) [ ]   Click the 'Add to Basket' button for Carrot Juice to add it to the cart.
112) [ ]   Click the 'Eggfruit Juice (500ml)' image to interact with the product.
113) [ ]   Click the 'Add to Basket' button for Eggfruit Juice to add it to the cart.
114) [ ]   Do this Click the 'Contact' link to navigate to the contact page.
115) [ ]   Do this Click the 'Company' link to navigate to the company page.
116) [ ]   Do this Click the 'OWASP Juice Shop' link to navigate to the OWASP Juice Shop page.
117) [ ]   Do this Click the 'v17.3.0' link to navigate to the version page.
118) [ ]   Do this Click the 'Contact' link to navigate to the contact page.
119) [ ]   Do this Click the 'Company' link to navigate to the company page.
120) [ ]   Do this Click the 'OWASP Juice Shop' link to navigate to the OWASP Juice Shop page.
121) [ ]   Do this Click the 'v17.3.0' link to navigate to the version page.
122) [ ]   Do this Click the 'Contact' link to navigate to the contact page.
123) [ ]   Do this Click the 'Company' link to navigate to the company page.
124) [ ]   Do this Click the 'OWASP Juice Shop' link to navigate to the OWASP Juice Shop page.
125) [ ]   Do this Click the 'v17.3.0' link to navigate to the version page.
126) [ ]   Do this Click the 'Contact' link to navigate to the contact page.
127) [ ]   Do this Click the 'Company' link to navigate to the company page.
128) [ ]   Do this Click the 'OWASP Juice Shop' link to navigate to the OWASP Juice Shop page.
129) [ ]   Do this Click the 'v17.3.0' link to navigate to the version page.
130) [ ]   Do this Click the 'Contact' link to navigate to the contact page.
131) [ ]   Do this Click the 'Company' link to navigate to the company page.
132) [ ]   Do this Click the 'OWASP Juice Shop' link to navigate to the OWASP Juice Shop page.
133) [ ]   Do this Click the 'v17.3.0' link to navigate to the version page.
134) [ ]   Do this Click the 'Contact' link to navigate to the contact page.
135) [ ]   Do this Click the 'Company' link to navigate to the company page.
136) [ ]   Do this Click the 'OWASP Juice Shop' link to navigate to the OWASP Juice Shop page.
137) [ ]   Do this Click the 'v17.3.0' link to navigate to the version page.
138) [ ]   Do this Click the 'Contact' link to navigate to the contact page.
139) [ ]   Do this Click the 'Company' link to navigate to the company page.
140) [ ]   Do this Click the 'OWASP Juice Shop' link to navigate to the OWASP Juice Shop page.
141) [ ]   Do this Click the 'v17.3.0' link to navigate to the version page.
142) [ ]   Do this Click the 'Contact' link to navigate to the contact page.
143) [ ]   Do this Click the 'Company' link to navigate to the company page.
144) [ ]   Do this Click the 'OWASP Juice Shop' link to navigate to the OWASP Juice Shop page.
145) [ ]   Do this Click the 'v17.3.0' link to navigate to the version page.
146) [ ]   Click the 'Fruit Press' image to interact with the product.
147) [ ]   Click the 'Green Smoothie' image to interact with the product.
148) [ ]   Click the 'Juice Shop "Permafrost" 2020 Edition' image to interact with the product.

Your goal is to update the plan if nessescary. This should happen for the following reasons:
1. the page has been dynamically updated, and a modification to the plan is required
Here are some requirements for updating plans:
- you can ONLY ADD plan-items
- you can NOT DELETE plan-items
- you can NOT MODIFY plan-items
Here is the previous page:
This application is riddled with security vulnerabilities. Your progress exploiting these is
tracked on a
Score Board
.
[0]<button title='Cancel the tutorial'>× />
[1]<mat-icon role='img'>search />
[2]<button aria-label='Show/hide account menu' aria-expanded='false'>account_circle
Account />
[3]<button aria-label='Show the shopping cart' href='/basket'>shopping_cart
Your Basket
0 />
[4]<button aria-label='Language selection menu' aria-expanded='false'>language
EN />
All Products
[5]<div >Apple Juice (1000ml)
1.99¤ />
    [6]<img role='button' alt='Apple Juice (1000ml)' />
[7]<button >Add to Basket />
[8]<div >Apple Pomace
0.89¤ />
    [9]<img role='button' alt='Apple Pomace' />
[10]<button >Add to Basket />
[11]<div >Banana Juice (1000ml)
1.99¤ />
    [12]<img role='button' alt='Banana Juice (1000ml)' />
[13]<button >Add to Basket />
[14]<div >Best Juice Shop Salesman Artwork
5000¤ />
    [15]<img role='button' alt='Best Juice Shop Salesman Artwork' />
[16]<button >Add to Basket />
[17]<div >Carrot Juice (1000ml)
2.99¤ />
    [18]<img role='button' alt='Carrot Juice (1000ml)' />
[19]<button >Add to Basket />
[20]<div >Eggfruit Juice (500ml)
8.99¤ />
    [21]<img role='button' alt='Eggfruit Juice (500ml)' />
[22]<button >Add to Basket />
[23]<div >Fruit Press
89.99¤ />
    [24]<img role='button' alt='Fruit Press' />
[25]<div >Green Smoothie
1.99¤ />
    [26]<img role='button' alt='Green Smoothie' />
[27]<div >Juice Shop "Permafrost" 2020 Edition
9999.99¤ />
    [28]<img role='button' alt='Juice Shop "Permafrost" 2020 Edition' />
Here is the current page:
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
Open side menu
Here are the actions to affect this change:
Successful - Clicked the 'Launch beginners tutorial' link to start the tutorial.

Return a list of plan-items to be added to the plan
    """
  }
]

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
  A plan was created to accomplish the goals above.
  Here is the original plan:

**NAVIGATION & INTERFACE:**
> **HEADER NAVIGATION:**
--> [*] Click the 'Open Sidenav' button to expand the side navigation menu.
--> [ ] Click the 'Back to homepage' button to navigate to the search page.
--> [ ] Click the 'Show/hide account menu' button to expand the account menu.
--> [ ] Click the 'Show the shopping cart' button to navigate to the basket page.
--> [ ] Click the 'Language selection menu' button to expand the language selection menu.

> **SEARCH FUNCTIONALITY:**
--> [*] Enter a search term into the search input field to trigger search functionality.
--> [*] Click the 'search' icon to trigger a search functionality.

**PRODUCT INTERACTIONS:**
> **JUICE PRODUCTS:**
--> [ ] Click the 'Apple Juice (1000ml)' image to trigger any associated functionality.
--> [ ] Click the 'Add to Basket' button for Apple Juice to add it to the shopping cart.
--> [ ] Click the 'Apple Pomace' image to trigger any associated functionality.
--> [ ] Click the 'Add to Basket' button for Apple Pomace to add it to the shopping cart.
--> [ ] Click the 'Banana Juice (1000ml)' image to trigger any associated functionality.
--> [ ] Click the 'Add to Basket' button for Banana Juice to add it to the shopping cart.
--> [ ] Click the 'Carrot Juice (1000ml)' image to trigger any associated functionality.
--> [ ] Click the 'Add to Basket' button for Carrot Juice to add it to the shopping cart.
--> [ ] Click the 'Eggfruit Juice (500ml)' image to trigger any associated functionality.
--> [ ] Click the 'Add to Basket' button for Eggfruit Juice to add it to the shopping cart.

> **OTHER PRODUCTS:**
--> [ ] Click the 'Best Juice Shop Salesman Artwork' image to trigger any associated functionality.
--> [ ] Click the 'Add to Basket' button for the Artwork to add it to the shopping cart.
--> [ ] Click the 'Fruit Press' image to trigger any associated functionality.
--> [ ] Click the 'Green Smoothie' image to trigger any associated functionality.
--> [ ] Click the 'Juice Shop "Permafrost" 2020 Edition' image to trigger any associated functionality.

**SITE NAVIGATION:**
> **INFORMATION PAGES:**
--> [*] Click the 'Go to contact us page' link to navigate to the contact page.
--> [ ] Click the 'Go to complain page' link to navigate to the complain page.
--> [ ] Click the 'Go to about us page' link to navigate to the about us page.

> **INTERACTIVE FEATURES:**
--> [ ] Click the 'Go to chatbot page' link to navigate to the chatbot page.
--> [ ] Click the 'Go to photo wall' link to navigate to the photo wall page.
--> [ ] Click the 'Go to deluxe membership page' link to navigate to the deluxe membership page.
--> [ ] Click the 'Launch beginners tutorial' link to trigger the tutorial functionality.

> **EXTERNAL LINKS:**
--> [ ] Click the 'Go to OWASP Juice Shop GitHub page' link to navigate to the GitHub page.

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
  Here is the current page:
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
  Return a list of plan-items to be added to the plan
    """
  }
]

MODELS = [openai_client]
# MODELS = [cohere_client, openai_client]
# MIXED = [cohere_client, deepseek_client]

for i in range(5):
    for client in MODELS:
        print(f"{i}. ### Using {client.__class__.__name__} ###")

        plan_items = update_plan_with_messages(cohere_client, PROMPT3)
        for item in plan_items:
            print(item.plan_item.plan)
