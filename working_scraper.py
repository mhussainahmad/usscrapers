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
    c4a_compile,
    CompilationResult
)

async def main():
    browser_config = BrowserConfig(
        headless=False,
        verbose=True,
    )
    
    # Store HTML content from all pages
    all_page_htmls = []
    session_id = "virginia_session"
    
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
    
    # Fill in the search form
    CLICK `#BEFilingSearch_txtFilingDateFrom`
    WAIT 2
    TYPE "07/21/2025"
    WAIT 2
    CLICK `#BEFilingSearch_txtFilingDateTo`
    TYPE "07/22/2025"
    WAIT 2
    CLICK `body > div.content-wrapper > section > form > div.row > div.col-md-5.col-sm-6.col-xs-12.text-right.label-align`
    
    # Verify the dates were set correctly
    EVAL `
    const fromField = document.querySelector('#BEFilingSearch_txtFilingDateFrom');
    const toField = document.querySelector('#BEFilingSearch_txtFilingDateTo');
    
    console.log("From date field value:", fromField ? fromField.value : "Field not found");
    console.log("To date field value:", toField ? toField.value : "Field not found");
    
    // Trigger change events to ensure validation runs
    if (fromField) {
        fromField.dispatchEvent(new Event('change', { bubbles: true }));
        fromField.dispatchEvent(new Event('blur', { bubbles: true }));
    }
    if (toField) {
        toField.dispatchEvent(new Event('change', { bubbles: true }));
        toField.dispatchEvent(new Event('blur', { bubbles: true }));
    }
    `
    WAIT 3
    
    # Click the search button
    CLICK `#btnSearch`
    
    # Wait for popup
    WAIT `body > div.sweet-alert.showSweetAlert.visible` 10
    
    IF (EXISTS `body > div.sweet-alert.showSweetAlert.visible`) THEN CLICK `body > div.sweet-alert.showSweetAlert.visible > div.sa-button-container > div > button`
    
    WAIT `#Listrow_grid_businessList` 10
    """

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First page - initial search
        crawler_config = CrawlerRunConfig(
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter()
            ),
            c4a_script=c4a_script,
            session_id=session_id
        )
        result: CrawlResult = await crawler.arun(
            url="https://cis.scc.virginia.gov/EntitySearch/Index", config=crawler_config
        )
        
        # Store the first page HTML
        if result.cleaned_html:
            all_page_htmls.append(result.cleaned_html)
            print(f"Stored HTML from page 1")
        else:
            print("Warning: No HTML content from page 1")
        
        # Now handle pagination - get all pages
        page = 2
        max_pages = 10  # Limit to prevent infinite loops
        
        while page <= max_pages:
            print(f"Processing page {page}...")
            
            # JavaScript to click next page button using the correct selector
            next_page_js = """
            const nextButton = document.querySelector('#pagination-digg > li:nth-child(9) > a');
            if (nextButton) {
                console.log('Found next button, clicking...');
                nextButton.click();
                return true;
            } else {
                console.log('No next button found');
                return false;
            }
            """
            
            try:
                next_page_config = CrawlerRunConfig(
                    js_code=next_page_js,
                    wait_for="css:#Listrow_grid_businessList",
                    js_only=True,  # This keeps the browser session open
                    session_id=session_id
                )
                
                next_result = await crawler.arun(
                    url="https://cis.scc.virginia.gov/EntitySearch/Index",
                    config=next_page_config
                )
                
                # Store this page's HTML
                if next_result.cleaned_html:
                    all_page_htmls.append(next_result.cleaned_html)
                    print(f"Stored HTML from page {page}")
                    
                    # Check if there are any entity IDs on this page
                    entity_ids_on_page = extract_entity_ids_from_html(next_result.cleaned_html)
                    if not entity_ids_on_page:
                        print(f"No entity IDs found on page {page}, stopping pagination")
                        break
                        
                    page += 1
                    await asyncio.sleep(2)  # Be respectful to the server
                else:
                    print(f"No HTML content from page {page}, stopping")
                    break
                    
            except Exception as e:
                print(f"Error on page {page}: {e}")
                break
        
        # Clean up the session
        await crawler.crawler_strategy.kill_session(session_id)
    
    # Extract entity IDs from all stored HTML
    all_entity_ids = []
    for i, html in enumerate(all_page_htmls, 1):
        if html:  # Check if HTML is not None
            print(f"Extracting entity IDs from page {i}...")
            page_entity_ids = extract_entity_ids_from_html(html)
            all_entity_ids.extend(page_entity_ids)
            print(f"Found {len(page_entity_ids)} entity IDs on page {i}")
        else:
            print(f"Skipping page {i} - no HTML content")
    
    print(f"\nTotal entity IDs found: {len(all_entity_ids)}")
    
    # Save all entity IDs to file
    with open('all_entity_ids.json', 'w') as f:
        json.dump({'entity_ids': all_entity_ids}, f, indent=2)
    
    print("All entity IDs saved to all_entity_ids.json")

def extract_entity_ids_from_html(html):
    """Extract entity IDs from HTML using regex patterns"""
    if not html:
        return []
        
    entity_ids = []
    
    # Look for entity IDs in various patterns
    patterns = [
        r'SeriesLLC\((\d+),',  # Onclick pattern
        r'entity_id=(\d+)',    # URL parameter pattern
        r'EntitySearch/Index\?id=(\d+)',  # URL pattern
        r'data-entity-id="(\d+)"',  # Data attribute pattern
    ]
    
    for pattern in patterns:
        try:
            matches = re.findall(pattern, html)
            entity_ids.extend(matches)
        except Exception as e:
            print(f"Error with pattern {pattern}: {e}")
            continue
    
    # Remove duplicates while preserving order
    seen = set()
    unique_entity_ids = []
    for entity_id in entity_ids:
        if entity_id not in seen:
            seen.add(entity_id)
            unique_entity_ids.append(entity_id)
    
    return unique_entity_ids

if __name__ == "__main__":
    asyncio.run(main())