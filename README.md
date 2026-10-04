# usscrapers

Python scrapers for the Virginia State Corporation Commission (SCC) business entity search, which collect entity IDs and basic entity details from public search results.

## Overview

The target is the SCC Clerk's Information System entity search at `https://cis.scc.virginia.gov/EntitySearch/Index`. The repository contains two approaches.

**1. HTTP requests and HTML parsing (`main.py`)**

- Fetches the search page and reads the ASP.NET `__RequestVerificationToken` from it.
- Sends POST requests (`isAllRecords`, then `pidx` for later pages) to page through results.
- Parses the `grid_businessList` table with BeautifulSoup and extracts entity IDs with a regex on the `SeriesLLC(<id>, ...)` onclick handlers.
- Requests the `BusinessInformation` page for each ID and tries to read entity name, type and status.
- Writes IDs to `entity_ids.txt` and details to `entity_details.csv`. Each response is also saved as `debug_page_<n>.html` for inspecting selectors.
- Waits 1 second between result pages and 2 seconds between detail requests.

The request headers in `main.py` contain a captured browser session cookie. Replace it with a fresh session before running. Only name, type and status are parsed so far, and the other CSV columns stay empty.

**2. Browser automation with Crawl4AI (`scraper.py`, `working_scraper.py`, `fixed_c4a_script.py`, `test_simple_script.py`)**

The SCC site's advanced search (filtering by filing date range) is driven through a datepicker and a modal confirmation dialog. These scripts use [Crawl4AI](https://github.com/unclecode/crawl4ai) and its C4A scripting language to:

- open the advanced search panel and set the "filing date from/to" fields,
- submit the search and dismiss the confirmation dialog,
- click through result pages in one browser session (`js_only` follow-up calls, up to 10 pages),
- extract entity IDs from the result rows (`JsonCssExtractionStrategy` in `scraper.py`, regex over cleaned HTML in `working_scraper.py`),
- save the collected IDs to `all_entity_ids.json`.

The scripts differ in how they set dates. Some click datepicker cells, others type or set the field values directly with JavaScript. Dates are hard-coded (July 2025 ranges) and need editing for other periods. `C4A_SCRIPT_ANALYSIS.md` documents the problems found with the first C4A script (brittle datepicker selectors, short waits, missing fallbacks) and proposes fixes. Note that `fixed_c4a_script.py` and `test_simple_script.py` pass their C4A scripts through `js_code` instead of `c4a_script`, so they do not run as written.

This is exploratory work. The committed `all_entity_ids.json` is empty, and no scraped output is included in the repository.

## Repository layout

```
main.py                  requests + BeautifulSoup scraper (IDs and entity details to CSV)
scraper.py               Crawl4AI scraper with date-range search and CSS extraction
working_scraper.py       Crawl4AI scraper that collects page HTML, then extracts IDs by regex
fixed_c4a_script.py      Revised C4A scripts (fixed / alternative / simple variants)
test_simple_script.py    Minimal C4A script for checking navigation and form filling
C4A_SCRIPT_ANALYSIS.md   Notes on C4A script issues and fixes
debug_page_1.html        Saved copy of the search page, used for selector debugging
all_entity_ids.json      Output file (currently empty)
pyproject.toml, uv.lock  Project metadata and locked dependencies
```

## Getting started

Requires Python 3.13 and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
uv run crawl4ai-setup          # installs the Playwright browser used by Crawl4AI

uv run python main.py          # requests-based scraper
uv run python working_scraper.py   # Crawl4AI date-range scraper
```

The Crawl4AI scripts run with `headless=False`, so a desktop session is needed to see the browser. `scraper.py` expects a proxy to be configured in its `BrowserConfig`. Remove that setting or supply your own proxy before running it.

The data comes from a public government registry. Check the site's terms of use and keep request rates low when running these scripts.

## Tech stack

Python 3.13, requests, BeautifulSoup, Crawl4AI (Playwright-based), Selenium (declared dependency), uv.
