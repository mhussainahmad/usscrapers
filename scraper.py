import asyncio
import json
import re
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    CrawlResult,
    RoundRobinProxyStrategy,
    c4a_compile,
    CompilationResult,
    ProxyConfig
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.cache_context import CacheMode

async def main():
    browser_config = BrowserConfig(
        headless=False,
        verbose=True,
        proxy="https://24.199.75.112:9989@finmtozcdx303317:d3MU8i4MaJc2GF7P"
    )
    proxy_strategy = RoundRobinProxyStrategy(
        [
            "https://24.199.75.112:9989@finmtozcdx303317:d3MU8i4MaJc2GF7P"
        ]
    )
    
    # Store all entity IDs
    all_entity_ids = []
    session_id = "virginia_session"
    
    # Define extraction schema for entity IDs
    schema = {
        "name": "Entity ID Extractor",
        "baseSelector": "tr",  # Table rows
        "fields": [
            {
                "name": "entity_id",
                "selector": "a[onclick*='SeriesLLC']",
                "type": "attribute",
                "attribute": "onclick"
            }
        ],
    }
    extraction_strategy = JsonCssExtractionStrategy(schema)
    
    # First page - perform search
    c4a_script = """
    # GO https://cis.scc.virginia.gov/EntitySearch/Index

    # Wait for page to load
    WAIT `body` 5
    
    # Wait for the advanced search link to appear and click it
    WAIT `#AdhvanceClk` 10
    CLICK `#AdhvanceClk > a`
    WAIT 3
    
    # Wait for the search form to appear
    WAIT `#BEFilingSearch_txtFilingDateFrom` 2
    SCROLL DOWN 500
    WAIT 5
    # Fill in the search form
    CLICK `#BEFilingSearch_txtFilingDateFrom`
    WAIT 2
    # TYPE "07/21/2025"
    CLICK `body > div.datepicker.datepicker-dropdown.dropdown-menu.datepicker-orient-left.datepicker-orient-top > div.datepicker-days > table > tbody > tr:nth-child(4) > td:nth-child(2)`
    WAIT 2
    CLICK `#BEFilingSearch_txtFilingDateTo`
    WAIT 2
    # TYPE "07/22/2025"
    CLICK `body > div.datepicker.datepicker-dropdown.dropdown-menu.datepicker-orient-left.datepicker-orient-top > div.datepicker-days > table > tbody > tr:nth-child(4) > td:nth-child(3)`
    WAIT 2
    
    # Click the search button
    CLICK `#btnSearch`
    
    # Wait for popup
    WAIT `body > div.sweet-alert.showSweetAlert.visible` 10
    
    IF (EXISTS `body > div.sweet-alert.showSweetAlert.visible`) THEN CLICK `body > div.sweet-alert.showSweetAlert.visible > div.sa-button-container > div > button`
    
    WAIT `#Listrow_grid_businessList` 10
    """

    # JavaScript for next page
    js_next_page = """document.querySelector('#pagination-digg > li:nth-child(9) > a').click();"""
    wait_for = """() => document.querySelectorAll('#Listrow_grid_businessList tr').length > 0"""

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Crawl multiple pages
        for page in range(10):  # Limit to 10 pages
            print(f"Processing page {page + 1}...")
            
            if page == 0:
                # First page - initial search
                config = CrawlerRunConfig(
                    session_id=session_id,
                    c4a_script=c4a_script,
                    markdown_generator=DefaultMarkdownGenerator(
                        content_filter=PruningContentFilter()
                    ),
                    # proxy_rotation_strategy=proxy_strategy
                )
            else:
                # Subsequent pages - click next and extract
                config = CrawlerRunConfig(
                    session_id=session_id,
                    js_code=js_next_page,
                    wait_for=wait_for,
                    js_only=True,
                    extraction_strategy=extraction_strategy,
                    cache_mode=CacheMode.BYPASS,
                    # proxy_rotation_strategy=proxy_strategy
                )
            
            try:
                result = await crawler.arun(
                    url="https://cis.scc.virginia.gov/EntitySearch/Index",
                    config=config
                )
                print(result.markdown.raw_markdown)
                if result.success and result.extracted_content:
                    # Parse the extracted content
                    extracted_data = json.loads(result.extracted_content)
                    print(f"Page {page + 1}: Found {len(extracted_data)} items")
                    
                    # Extract entity IDs from onclick attributes
                    page_entity_ids = []
                    for item in extracted_data:
                        if item.get('entity_id'):
                            onclick = item['entity_id']
                            # Extract entity ID from onclick like "SeriesLLC(11873673,'Limited Liability Company','False');"
                            match = re.search(r'SeriesLLC\((\d+),', onclick)
                            if match:
                                entity_id = match.group(1)
                                page_entity_ids.append(entity_id)
                    
                    if page_entity_ids:
                        all_entity_ids.extend(page_entity_ids)
                        print(f"Page {page + 1}: Found {len(page_entity_ids)} entity IDs")
                    else:
                        print(f"No entity IDs found on page {page + 1}, stopping pagination")
                        break
                else:
                    print(f"No data extracted from page {page + 1}, stopping")
                    break
                    
            except Exception as e:
                print(f"Error on page {page + 1}: {e}")
                break
        
        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
    
    print(f"\nTotal entity IDs found: {len(all_entity_ids)}")
    
    # Save all entity IDs to file
    with open('all_entity_ids.json', 'w') as f:
        json.dump({'entity_ids': all_entity_ids}, f, indent=2)
    
    print("All entity IDs saved to all_entity_ids.json")
    return all_entity_ids

if __name__ == "__main__":
    asyncio.run(main())