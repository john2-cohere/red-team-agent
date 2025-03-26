#!/usr/bin/env python3
"""
Password Reset Flow Navigation Script

This script automates the password reset flow on the local authentication server.
"""
import asyncio
import logging
from browser_use.browser.browser import Browser, BrowserConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def init_browser():
    # Initialize browser with custom config
    browser_config = BrowserConfig(
        headless=False,  # Set to False to see the browser window
        disable_security=True,
        extra_chromium_args=[
            "--window-size=1920,1080",
        ],
        _force_keep_browser_alive=True
    )
    
    browser = Browser(config=browser_config)
    # Get the playwright browser
    playwright_browser = await browser.get_playwright_browser()
    print("[PLATYWRIGHT BROWSER]", playwright_browser)
    # Create a browser context
    context = await playwright_browser.new_context()
    
    # Register request handler at context level
    async def handle_request(route):
        request = route.request
        print(f"\nRequest: {request.method} {request.url}")
        # print(f"Headers: {request.headers}")
        # print(f"Post Data: {request.post_data}")
        
        # Get the response after continuing the route
        await route.continue_()
        # response = await request.response()
        # if response:
        #     print(f"Response Status: {response.status}")
        #     try:
        #         print(f"Response Body: {await response.text()}")
        #     except:
        #         print("Could not get response body")
        #     print(f"Response Headers: {response.headers}")

    await context.route("**/*", handle_request)
    
    # Create a new page
    page = await context.new_page()

    return browser, page

async def navigate_password_reset():
    browser, page = await init_browser()
    try:
        # Navigate to login page
        logger.info("Navigating to login page")
        await page.goto("http://localhost:5000/login", timeout=30000, wait_until="networkidle")
        
        # Click on forgot password link
        logger.info("Clicking forgot password link")
        await page.click("text=Forgot Password?")
        await page.wait_for_load_state("networkidle") 
        
        # Fill in email for password reset
        logger.info("Entering email for password reset")
        await page.fill("#attackerEmail", "test@example.com")
        
        # Submit the form
        logger.info("Submitting password reset form")
        await page.click("text=Send Reset Link")
        await page.wait_for_load_state("networkidle")
        
        # Keep the script running to prevent browser from closing
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error during navigation: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(navigate_password_reset())