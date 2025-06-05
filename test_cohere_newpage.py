from pydantic import BaseModel
from typing import List, Dict, ClassVar
import enum
import json

from langchain_cohere import ChatCohere
from browser_use.controller.registry.views import ActionModel

class NewPageStatus(str, enum.Enum):
	SAME_PAGE = "same_page"
	NEW_PAGE = "new_page"
	UPDATED_PAGE = "updated_page"

LLM_MSGS = [
  {
    "role": "user",
    "content": """
  
  You are presented with the following views from a browser
  Here is the CURR_PAGE:
  URL: http://localhost:3000/#/
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
  
  Here is the PREV_PAGE:
  URL: http://localhost:3000/#/
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
  
  Given the different views, determine if the CURR_PAGE is a:
  
  1. new_page: different page of the application
  2. updated_page: same page of the application, but with an updated view (ie. submenu expansion, pop-up)
  
  Some things to keep in mind:
  1. visible elements: the view presented only shows visible elements in the DOM; so elements that are on the same page might not be displayed because is_top_element == False or is_in_viewport == False
  
  Which is why when considering whether the CURR_PAGE is a new_page or updated_page, make your decision by considering both the url and the DOM of the CURR_PAGE
  Now make your choices
    """
  }
]

for i in range(10):
    client = ChatCohere(model="command-a-03-2025")
    response = client.invoke(
        LLM_MSGS, 
        response_format={
            "type": "json_object",
            "schema": {
                "type": "object",
                "required": ["page_status"],
                "properties": {
                    "page_status": {
                        "type": "string",
                        "enum": [status.value for status in NewPageStatus],
                        "description": "The status indicating if this is a new page or updated view"
                    }
                }
            }
        }
    )
    print(response.content)