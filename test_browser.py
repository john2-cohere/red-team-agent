#!/usr/bin/env python3
"""
Google Browser Navigation Script

This script uses the custom Browser class to open Google.ca in a browser window
and keeps it open.
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
        proxy_server="http://3.146.217.192:3128",
        _force_keep_browser_alive=True
    )
    
    browser = Browser(config=browser_config)
    # Create a new browser context with default config
    context = await browser.get_playwright_browser()
    
    # Create a new page
    page = await context.new_page()
    return browser, page

async def navigate_to_google():
    browser, page = await init_browser()
    try:
        # Navigate to Google.ca
        logger.info("Navigating to Google.ca")
        await page.goto("https://www.google.ca", timeout=30000, wait_until="networkidle")
        
        # Keep the script running to prevent browser from closing
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error during navigation: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(navigate_to_google())
