import requests
from bs4 import BeautifulSoup, Tag
import csv
import time
import re
from typing import List, Optional

def contains_text(text: str, search_text: str) -> bool:
    """Helper function to check if text contains search_text"""
    return bool(text and search_text in text)

def get_entity_ids_from_page(soup: BeautifulSoup) -> List[str]:
    """Extract entity IDs from a single page"""
    entity_ids = []
    table = soup.find('table', {'id': 'grid_businessList'})
    
    if table is None or not isinstance(table, Tag):
        print("No table found on this page")
        return entity_ids
    
    rows = table.find_all('tr')[1:]  # Skip header row
    
    for row in rows:
        if row is not None and isinstance(row, Tag):
            # Look for links that contain entity IDs in Onclick attributes
            links = row.find_all('a')
            for link in links:
                if isinstance(link, Tag):
                    onclick = link.get('Onclick', '')
                    if onclick:
                        # Extract entity ID from Onclick like "SeriesLLC(11873673,'Limited Liability Company','False');"
                        match = re.search(r'SeriesLLC\((\d+),', str(onclick))
                        if match:
                            entity_id = match.group(1)
                            entity_ids.append(entity_id)
                            break  # Only get the first entity ID per row
    
    return entity_ids

def get_all_entity_ids() -> List[str]:
    """Get entity IDs from all available pages"""
    base_url = "https://cis.scc.virginia.gov/EntitySearch/Index"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "connection": "keep-alive",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": "ASP.NET_SessionId=vzz5xwx3x124ev4i5zws1eiy; __RequestVerificationToken=PRPU1HD_a3m6X2Z0HGrJN6A3NRHJfPbetgrT4RuXQVDhs3Keus5RX1k4lT9l18LzLbfrjrIca09T0MNFESjlGNixbQVufFf73-CFANPC5wE1; nmstat=c2a03b9d-2ed8-bf02-6a7f-442d6b05a771",
        "host": "cis.scc.virginia.gov",
        "origin": "https://cis.scc.virginia.gov",
        "referer": "https://cis.scc.virginia.gov/EntitySearch/Index",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"
    }
    
    all_entity_ids = []
    page = 1
    
    while True:
        print(f"Scraping page {page}...")
        
        # Get the initial page to get the verification token
        if page == 1:
            print("Getting initial page...")
            response = requests.get(base_url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to get initial page: {response.status_code}")
                break
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Save the initial page HTML for debugging
            with open(f'debug_page_{page}.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"Saved initial page HTML to debug_page_{page}.html")
            
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            if token_input is None or not isinstance(token_input, Tag):
                print("Could not find verification token")
                break
            verification_token = token_input.get('value', '')
            print(f"Found verification token: {verification_token[:20] if verification_token else 'None'}...")
            
            # Get all records
            data = {
                "isBack": "true",
                "isAllRecords": "true",
                "__RequestVerificationToken": verification_token
            }
        else:
            # For subsequent pages, use pidx parameter for pagination
            data = {
                "pidx": str(page),
                "__RequestVerificationToken": verification_token
            }
        
        print(f"Making POST request with data: {data}")
        response = requests.post(base_url, headers=headers, data=data)
        
        if response.status_code != 200:
            print(f"Failed to get page {page}: {response.status_code}")
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save the response HTML for debugging
        with open(f'debug_page_{page}.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"Saved page {page} HTML to debug_page_{page}.html")
        
        page_entity_ids = get_entity_ids_from_page(soup)
        
        if not page_entity_ids:
            print(f"No more entity IDs found on page {page}")
            break
            
        all_entity_ids.extend(page_entity_ids)
        print(f"Found {len(page_entity_ids)} entity IDs on page {page}")
        
        # Check if there's a next page
        next_link = soup.find('a', string=lambda text: contains_text(str(text), 'Next'))
        if not next_link:
            print("No more pages found")
            break
            
        page += 1
        time.sleep(1)  # Be respectful to the server
    
    print(f"Total entity IDs collected: {len(all_entity_ids)}")
    return all_entity_ids

def get_entity_details(entity_id: str) -> Optional[dict]:
    """Get detailed information for a specific entity"""
    url = f"https://cis.scc.virginia.gov/EntitySearch/BusinessInformation?businessId={entity_id}&source=FromEntityResult&isSeries%20=%20false"
    
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "connection": "keep-alive",
        "host": "cis.scc.virginia.gov",
        "referer": "https://cis.scc.virginia.gov/EntitySearch/Index",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract entity details - this will need to be customized based on the actual page structure
            details = {
                'entity_id': entity_id,
                'entity_name': '',
                'entity_type': '',
                'status': '',
                'formation_date': '',
                'principal_office': '',
                'registered_agent': '',
                'raw_html': response.text  # Store raw HTML for manual inspection
            }
            
            # Try to extract common fields - adjust selectors based on actual page structure
            name_elem = soup.find('span', string=lambda text: contains_text(str(text), 'Entity Name'))
            if name_elem and isinstance(name_elem, Tag) and name_elem.find_next_sibling():
                next_sibling = name_elem.find_next_sibling()
                if isinstance(next_sibling, Tag):
                    details['entity_name'] = next_sibling.get_text(strip=True)
            
            type_elem = soup.find('span', string=lambda text: contains_text(str(text), 'Entity Type'))
            if type_elem and isinstance(type_elem, Tag) and type_elem.find_next_sibling():
                next_sibling = type_elem.find_next_sibling()
                if isinstance(next_sibling, Tag):
                    details['entity_type'] = next_sibling.get_text(strip=True)
            
            status_elem = soup.find('span', string=lambda text: contains_text(str(text), 'Status'))
            if status_elem and isinstance(status_elem, Tag) and status_elem.find_next_sibling():
                next_sibling = status_elem.find_next_sibling()
                if isinstance(next_sibling, Tag):
                    details['status'] = next_sibling.get_text(strip=True)
            
            return details
        else:
            print(f"Failed to get details for entity {entity_id}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error getting details for entity {entity_id}: {e}")
        return None

def scrape_virginia_entity_search():
    """Main function to scrape all entity IDs and their details"""
    print("Starting Virginia entity search scraper...")
    
    # Step 1: Get all entity IDs
    print("Step 1: Collecting all entity IDs...")
    entity_ids = get_all_entity_ids()
    
    if not entity_ids:
        print("No entity IDs found. Exiting.")
        return
    
    # Save entity IDs to a file for reference
    with open('entity_ids.txt', 'w') as f:
        for entity_id in entity_ids:
            f.write(f"{entity_id}\n")
    
    print(f"Saved {len(entity_ids)} entity IDs to entity_ids.txt")
    
    # Step 2: Get details for each entity
    print("Step 2: Getting detailed information for each entity...")
    
    with open('entity_details.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Entity ID', 'Entity Name', 'Entity Type', 'Status', 'Formation Date', 'Principal Office', 'Registered Agent'])
        
        for i, entity_id in enumerate(entity_ids, 1):
            print(f"Processing entity {i}/{len(entity_ids)}: {entity_id}")
            
            details = get_entity_details(entity_id)
            if details:
                writer.writerow([
                    details['entity_id'],
                    details['entity_name'],
                    details['entity_type'],
                    details['status'],
                    details['formation_date'],
                    details['principal_office'],
                    details['registered_agent']
                ])
            
            # Be respectful to the server
            time.sleep(2)
    
    print("Entity details saved to entity_details.csv")
    print("Raw HTML files saved for manual inspection")

if __name__ == "__main__":
    scrape_virginia_entity_search()
