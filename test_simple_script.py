import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Simple test script
test_script = """
GO https://cis.scc.virginia.gov/EntitySearch/Index
WAIT 5
EVAL `console.log("Page loaded:", document.title)`

# Wait for the page to load and look for the advanced search link
WAIT `#AdhvanceClk` 10
EVAL `console.log("Advanced search link found")`
CLICK `#AdhvanceClk > a`
WAIT 3

# Wait for the search form to appear
WAIT `#BEFilingSearch_txtFilingDateFrom` 10
EVAL `console.log("Search form loaded")`

# Scroll down to see the form
SCROLL DOWN 500
WAIT 2

# Simple JavaScript to set dates
EVAL `
console.log("Setting date fields...");
const fromField = document.querySelector('#BEFilingSearch_txtFilingDateFrom');
const toField = document.querySelector('#BEFilingSearch_txtFilingDateTo');

if (fromField) {
    fromField.value = '07/16/2025';
    console.log("From date set to:", fromField.value);
}

if (toField) {
    toField.value = '07/18/2025';
    console.log("To date set to:", toField.value);
}
`

WAIT 2

# Look for and click the search button
WAIT `#btnSearch` 5
CLICK `#btnSearch`
WAIT 5

EVAL `console.log("Search button clicked")`
WAIT 10
EVAL `console.log("Final page title:", document.title)`
"""

async def run_test_script():
    """Run the test script"""
    config = CrawlerRunConfig(
        js_code=test_script,
        wait_for="table, tbody, [class*='row']"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://cis.scc.virginia.gov/EntitySearch/Index", config=config)
        print("Test script result:")
        print(result.markdown)
        return result

if __name__ == "__main__":
    asyncio.run(run_test_script()) 