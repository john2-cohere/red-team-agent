#!/usr/bin/env python3
"""
HackerOne Report URL Scraper

This script uses the custom Browser class to fetch HackerOne Hacktivity page,
find all report URLs using regex, and print them.
"""

import asyncio
import re
import logging
import time
import random
import json
from browser_use.browser.browser import Browser, BrowserConfig
from pydantic import BaseModel, Field
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OUT_DIR = "scrapers/reports"
REPORT_PAGE = "https://hackerone.com/hacktivity/overview?queryString=disclosed%3Atrue&sortField=latest_disclosable_activity_at&sortDirection=DESC&pageIndex={index}"
REPORT_TIMEOUT = 10000

class ReportContent(BaseModel):
    reported_to: str
    reported_by: str
    title: str
    content: str | None = None
    severity: str | None = None
    bounty: float | None = None
    weaknesses: List[str] = Field(default_factory=list)
    screenshots: Dict[str, str] = Field(default_factory=dict)

def process_content(content):
    FILTER_OUT = ["Unwrap lines Copy Download"]

    content_str = ""
    screenshots = {}
    image_id = 0
    for line in content.split("\n"):
        if any(f in line for f in FILTER_OUT):
            continue

        if re.search(r"s3.*\.amazonaws\.com", line):
            name = "image_" + str(image_id)
            screenshots[name] = line
            content_str += "<" + name + ">" + "\n"
            image_id += 1
        else:
            content_str += line + "\n"

    return ReportContent(
        reported_to="",
        reported_by="",
        title="",
        content=content_str,
        severity=None,
        bounty=None,
        weaknesses=[],
        screenshots=screenshots
    )

async def parse_report_metadata(page) -> Tuple[str, str, str, str | None, float | None, List[str]]:    
    return None
    # return reported_to, reported_by, title, severity, bounty, weaknesses

async def parse_report_block(element, class_name):
    content = ""
    code_block = await element.query_selector(".interactive-markdown__code")
    if code_block:
        # Handle code blocks
        code_content = await element.query_selector(".interactive-markdown__code__content.interactive-markdown__code__content__wrap")
        if code_content:
            # Get spans without line numbers
            code_spans = await code_content.query_selector_all("span:not([class*='linenumber'])")
            for span in code_spans:
                span_text = await span.inner_text()
                content += span_text
            content += "\n"
        # Handle image blocks
        else:
            print("PARSING AS IMAGE")
            # Look for images recursively
            img = await element.query_selector("img")
            if img:
                src = await img.get_attribute("src")
                print("FOUND IMAGE SRC: ", src)
                content += src + "\n"
    else:
        try:
            # Extract inner text for paragraphs and user content
            text = await element.inner_text()
            print(element)
            print("INNER TEXT", text)
            content += text + "\n"
        except:
            pass

    return content

async def extract_report_content(page, report_url):
    """
    Extract content from a HackerOne report page by finding the interactive-markdown element
    and its child elements.
    """                    
    await page.goto(report_url, timeout=30000, wait_until="networkidle")

    content = ""
    try:
        # Wait for the interactive-markdown element to load
        await page.wait_for_selector("div[class='interactive-markdown']", timeout=REPORT_TIMEOUT)
        
        # TODO: currently we are only getting the first comment of the report and
        # ignoring followup comments
        # Get the interactive-markdown element
        markdown_element = await page.query_selector("div[class='interactive-markdown']")
        if markdown_element:
            # Get all child elements
            child_elements = await markdown_element.query_selector_all(">*")

            # Extract content based on element class
            for element in child_elements:
                class_name = await element.get_attribute("class")
                
                # Handle list elements (ul, ol)
                tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                if tag_name in ["ul", "ol"]:
                    list_items = await element.query_selector_all("li")
                    for item in list_items:
                        # Try to get class, but process item regardless
                        item_class = await item.get_attribute("class") or ""
                        block = await parse_report_block(item, item_class)                        
                        if block:
                            content += block
                else:
                    content += await parse_report_block(element, class_name)
        
        # reported_to, reported_by, title, severity, bounty, weaknesses = await parse_report_metadata(page)
        return process_content(content)
    
    except Exception as e:
        logger.error(f"Error extracting report content: {e}")

async def init_browser():
    # Initialize browser with custom config
    browser_config = BrowserConfig(
        headless=False,  # Set to True for headless mode
        disable_security=True,
        extra_chromium_args=[
            "--window-size=1920,1080",
        ]
    )
    
    browser = Browser(config=browser_config)
    # Create a new browser context with default config
    context = await browser.get_playwright_browser()
    
    # Create a single page that we'll reuse
    page = await context.new_page()
    return browser, page

async def scrape_reports(start_index=0):
    """
    Extract report URLs from HackerOne Hacktivity page
    """
    # Initialize browser with custom config
    browser_config = BrowserConfig(
        headless=False,  # Set to True for headless mode
        disable_security=True,
        extra_chromium_args=[
            "--window-size=1920,1080",
        ]
    )
    browser = Browser(config=browser_config)
    try:
        # Create a new browser context with default config
        context = await browser.get_playwright_browser()
        
        # Create a single page that we'll reuse
        page = await context.new_page()
        
        for i in range(start_index, 400):
            target_url = REPORT_PAGE.format(index=i)
            
            # Navigate to HackerOne Hacktivity page using existing page
            logger.info(f"Navigating to {target_url}")
            
            # Set a longer timeout for navigation (30 seconds)
            await page.goto(target_url, timeout=30000, wait_until="networkidle")
            
            # Wait for content to load
            logger.info("Waiting for content to load...")
            await page.wait_for_selector("div.pb-spacing-12.md\\:pb-0", timeout=30000)
            
            # Get the page content
            content = await page.content()
            
            # Extract report URLs using regex
            logger.info("Extracting report URLs...")
            pattern = r'href="/reports/(\d+)"'
            matches = re.findall(pattern, content)
            
            if not matches:
                logger.warning("No report URLs found. The page might have changed structure.")
                        
            # Print unique report URLs
            unique_ids = set(matches)
            logger.info(f"Found {len(unique_ids)} unique report URLs")
            errord_reports = []
            for report_id in unique_ids:
                try:
                    report_url = f"https://hackerone.com/reports/{report_id}"
                    content = await extract_report_content(page, report_url)

                    with open(f"{OUT_DIR}/{report_id}.json", "w") as f:
                        json.dump(content, f, indent=2)

                    # return unique_ids
                    time.sleep(max(0, random.normalvariate(2, 1.4)))
                except Exception as e:
                    logger.error(f">>>>>>>>>>> ??? >>>> Error processing report {report_url}: {e}", exc_info=True)
                    errord_reports.append(report_url)
                    continue

        # Close the page after the loop
        await page.close()

        with open("errord_reports.txt", "w") as f:
            f.write("\n".join(errord_reports))
            
    except Exception as e:
        logger.error(f"Error extracting report URLs: {e}")
        with open("last_url.txt", "w") as f:
            f.write(target_url)
        raise
    finally:
        # Close the browser
        logger.info("Closing browser...")
        await browser.close()

async def main():
    """Main function to run the script"""
    await scrape_reports(start_index=94)

if __name__ == "__main__":
    async def test_reports():
        browser, page = await init_browser()
        TEST_URLS = [
            # "https://hackerone.com/reports/1032610"
            # "https://hackerone.com/reports/1032610"
            # "https://hackerone.com/reports/1457471"
            "https://hackerone.com/reports/1237321"
        ]
        
        for url in TEST_URLS:
            report_content = await extract_report_content(page, url)
            print(report_content.content)
        
        await browser.close()

    asyncio.run(test_reports())