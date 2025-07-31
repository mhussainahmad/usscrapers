import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Fixed C4A Script for Virginia Entity Search
fixed_script = """
GO https://cis.scc.virginia.gov/EntitySearch/Index
WAIT 5
EVAL `console.log("Page loaded:", document.title)`

# Wait for the page to load and look for the advanced search link
WAIT `#AdhvanceClk` 10
CLICK `#AdhvanceClk > a`
WAIT 3

# Wait for the search form to appear
WAIT `#BEFilingSearch_txtFilingDateFrom` 10
EVAL `console.log("Search form loaded")`

# Scroll down to see the form
SCROLL DOWN 500
WAIT 2

# Fill in date fields directly with JavaScript
EVAL `
// Set the date fields directly
const fromDateField = document.querySelector('#BEFilingSearch_txtFilingDateFrom');
const toDateField = document.querySelector('#BEFilingSearch_txtFilingDateTo');

if (fromDateField) {
    fromDateField.value = '07/16/2025';
    fromDateField.dispatchEvent(new Event('change', { bubbles: true }));
    console.log("From date set");
}

if (toDateField) {
    toDateField.value = '07/18/2025';
    toDateField.dispatchEvent(new Event('change', { bubbles: true }));
    console.log("To date set");
}
`

WAIT 2

# Look for and click the search button
WAIT `#btnSearch` 5
CLICK `#btnSearch`
WAIT 5

# Check for and handle any alerts
IF (EXISTS `body > div.sweet-alert.showSweetAlert.visible`) THEN 
    CLICK `body > div.sweet-alert.showSweetAlert.visible > div.sa-button-container > button`
    WAIT 2

# Wait for any results to appear - be more flexible
WAIT 10
EVAL `console.log("Search completed. Current page title:", document.title)`
EVAL `console.log("Tables found:", document.querySelectorAll('table').length)`
EVAL `console.log("Table rows found:", document.querySelectorAll('tbody tr').length)`
EVAL `console.log("All elements with 'row' in class:", document.querySelectorAll('[class*="row"]').length)`
"""

# Alternative script that focuses on the search form without date selection
alternative_script = """
GO https://cis.scc.virginia.gov/EntitySearch/Index
WAIT 5
EVAL `console.log("Page loaded:", document.title)`

# Wait for the page to load and look for the advanced search link
WAIT `#AdhvanceClk` 10
CLICK `#AdhvanceClk > a`
WAIT 3

# Wait for the search form to appear
WAIT `#BEFilingSearch_txtFilingDateFrom` 10
EVAL `console.log("Search form loaded")`

# Scroll down to see the form
SCROLL DOWN 500
WAIT 2

# Fill in date fields directly with JavaScript
EVAL `
// Set the date fields directly
const fromDateField = document.querySelector('#BEFilingSearch_txtFilingDateFrom');
const toDateField = document.querySelector('#BEFilingSearch_txtFilingDateTo');

if (fromDateField) {
    fromDateField.value = '07/16/2025';
    fromDateField.dispatchEvent(new Event('change', { bubbles: true }));
    console.log("From date set");
}

if (toDateField) {
    toDateField.value = '07/18/2025';
    toDateField.dispatchEvent(new Event('change', { bubbles: true }));
    console.log("To date set");
}
`

WAIT 2

# Look for and click the search button
WAIT `#btnSearch` 5
CLICK `#btnSearch`
WAIT 5

# Check for and handle any alerts
IF (EXISTS `body > div.sweet-alert.showSweetAlert.visible`) THEN 
    CLICK `body > div.sweet-alert.showSweetAlert.visible > div.sa-button-container > button`
    WAIT 2

# Wait for any results to appear - be more flexible
WAIT 10
EVAL `console.log("Search completed. Current page title:", document.title)`
EVAL `console.log("Tables found:", document.querySelectorAll('table').length)`
EVAL `console.log("Table rows found:", document.querySelectorAll('tbody tr').length)`
EVAL `console.log("All elements with 'row' in class:", document.querySelectorAll('[class*="row"]').length)`
"""

# Simple script that just navigates and waits for the form
simple_script = """
GO https://cis.scc.virginia.gov/EntitySearch/Index
WAIT 5
EVAL `console.log("Page loaded:", document.title)`

# Wait for the page to load and look for the advanced search link
WAIT `#AdhvanceClk` 10
CLICK `#AdhvanceClk > a`
WAIT 3

# Wait for the search form to appear
WAIT `#BEFilingSearch_txtFilingDateFrom` 10
EVAL `console.log("Search form loaded")`

# Scroll down to see the form
SCROLL DOWN 500
WAIT 5

# Just wait for the page to load completely
EVAL `console.log("Page loaded. Available elements:", document.querySelectorAll('input, select, button').length)`
EVAL `console.log("Form elements found:", document.querySelectorAll('form').length)`
"""

async def run_fixed_script():
    """Run the fixed C4A script"""
    config = CrawlerRunConfig(
        js_code=fixed_script,
        wait_for="table, tbody, [class*='row']"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://cis.scc.virginia.gov/EntitySearch/Index", config=config)
        print("Fixed script result:")
        print(result.markdown)
        return result

async def run_alternative_script():
    """Run the alternative C4A script"""
    config = CrawlerRunConfig(
        js_code=alternative_script,
        wait_for="table, tbody, [class*='row']"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://cis.scc.virginia.gov/EntitySearch/Index", config=config)
        print("Alternative script result:")
        print(result.markdown)
        return result

async def run_simple_script():
    """Run the simple C4A script"""
    config = CrawlerRunConfig(
        js_code=simple_script,
        wait_for="form, input, select"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://cis.scc.virginia.gov/EntitySearch/Index", config=config)
        print("Simple script result:")
        print(result.markdown)
        return result

if __name__ == "__main__":
    # Run the fixed script
    asyncio.run(run_fixed_script()) 