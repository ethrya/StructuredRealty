import re
import time
import pickle
import multiprocessing
from functools import partial
from typing import Tuple, Optional, List, Dict, Any

# Data Handling
import pandas as pd
# Removed pyarrow imports for simplicity unless strictly needed for specific parquet options

# Selenium Imports
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
# from selenium.webdriver.common.keys import Keys # Not used in provided snippet
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from helpers.domain_scrapers import get_bed_bath_park_data, get_element_html_by_class, get_listing_info

# --- Configuration ---
CONFIG = {
    "suburbs": "campbell-act-2612,reid-act-2612,braddon-act-2612,ainslie-act-2602,dickson-act-2602,lyneham-act-2602,o-connor-act-2602,turner-act-2612,downer-act-2602,watson-act-2602,hackett-act-2602",
    "conditions": "&bedrooms=2&excludepricewithheld=1", # Keep as string or parse if needed
    "n_pages": 50, # How many search results pages to scrape
    "geckodriver_path": '/usr/local/bin/geckodriver', # Adjust path as needed
    "firefox_path": "/Applications/Firefox.app/Contents/MacOS/firefox", # Adjust path as needed
    "output_dir": "outdata", # Ensure this directory exists
    "listing_link_pattern": r"https://www\.domain\.com\.au/\w+-.+-act-\d{4}-\d{10}", # ACT specific
    # Locator for links on search results page - **NEEDS INSPECTION & ADJUSTMENT**
    "listing_link_locator": (By.XPATH, "//a[@href]"),
    # Locator for verifying search results page loaded - **NEEDS INSPECTION & ADJUSTMENT**
    "search_results_loaded_locator": (By.CSS_SELECTOR, "ul[data-testid='results']"),
    "num_workers": max(1, multiprocessing.cpu_count() - 1), # Number of parallel workers
    "worker_headless": True, # Run worker browsers headless
    "worker_page_load_strategy": 'eager', # Use 'eager' or 'normal' for workers
    "main_driver_page_load_strategy": 'eager', # Strategy for the main driver gathering links
    "main_driver_timeout": 30, # Page load timeout for main driver
    "wait_timeout": 20 # Default explicit wait timeout
}


# --- Helper Functions ---

def wait_for_element(
    driver: WebDriver,
    locator: Tuple[By, str],
    timeout: int = CONFIG["wait_timeout"],
    condition = EC.presence_of_element_located
    ) -> Optional[WebElement]:
    """Waits for a specific element, returns element or None."""
    # print(f"Waiting ({timeout}s) for: {locator} using {condition.__name__}") # Verbose logging
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(condition(locator))
        # print(f"Element found: {locator}") # Verbose logging
        return element
    except TimeoutException:
        print(f"Timed out waiting for element: {locator}")
        return None
    except Exception as e:
        print(f"Error during explicit wait for {locator}: {e}")
        return None


def scrape_single_listing(link: str, config_dict: dict) -> Optional[Dict[str, Any]]:
    """
    Worker function: Initializes a driver, scrapes a single listing, quits driver.
    """
    driver = None # Initialize driver to None
    service = None
    options = None
    print(f"Worker started for link: {link}")
    try:
        # --- Setup driver inside the worker ---
        service = FirefoxService(executable_path=config_dict['geckodriver_path'])
        options = FirefoxOptions()
        options.page_load_strategy = config_dict['worker_page_load_strategy']

        if config_dict['worker_headless']:
            options.add_argument("--headless")
        # Add other options like user-agent if needed
        # options.add_argument("--window-size=1920,1080")

        driver = webdriver.Firefox(service=service, options=options)
        # No page load timeout set here, rely on explicit waits in get_listing_info

        # --- Perform scraping ---
        listing_data = get_listing_info(driver, link) # Call the (placeholder) scraping logic

        return listing_data # Can be None if get_listing_info failed

    except Exception as e:
        print(f"CRITICAL WORKER ERROR scraping {link}: {e}")
        # Log the full traceback here if needed: import traceback; traceback.print_exc()
        return None # Return None on critical worker errors
    finally:
        # --- Ensure driver is quit ---
        if driver:
            print(f"Worker quitting driver for link: {link}")
            driver.quit()
        else:
            print(f"Worker finished (no driver to quit) for link: {link}")


def gather_listing_links(config_dict: dict) -> List[str]:
    """
    Sequentially navigates search results pages and gathers all listing links.
    """
    all_listing_links = []
    driver = None
    service = None
    options = None

    domain_base_page = f"https://www.domain.com.au/sold-listings/?suburb={config_dict['suburbs']}{config_dict['conditions']}&page="
    domain_pages = [domain_base_page + str(i+1) for i in range(config_dict['n_pages'])]
    link_pattern = re.compile(config_dict['listing_link_pattern'])

    print("--- Phase 1: Gathering Listing Links ---")
    try:
        service = FirefoxService(executable_path=config_dict['geckodriver_path'])
        options = FirefoxOptions()
        options.binary_location = config_dict['firefox_path']
        options.page_load_strategy = config_dict['main_driver_page_load_strategy']
        # options.add_argument("--headless") # Optional: Run main driver headless too

        driver = webdriver.Firefox(service=service, options=options)
        driver.set_page_load_timeout(config_dict['main_driver_timeout'])

        for page_url in domain_pages:
            print(f"Navigating to search page: {page_url}")
            try:
                driver.get(page_url)
            except selenium.common.exceptions.TimeoutException:
                print(f"Main driver timed out loading {page_url}. Continuing...")
                # Check if essential elements are loaded even after timeout
            except Exception as e:
                print(f"Error navigating to {page_url}: {e}. Skipping page.")
                continue

            # Wait for search results container to indicate page is usable
            if not wait_for_element(driver, config_dict['search_results_loaded_locator'], timeout=config_dict['wait_timeout']):
                 print(f"Results container not found on {page_url}. Skipping page.")
                 continue

            # Find link elements using the specific locator
            link_elements = driver.find_elements(*config_dict['listing_link_locator']) # Use '*' to unpack the tuple
            page_links = [elem.get_attribute("href") for elem in link_elements if elem.get_attribute("href")]

            # Filter using regex (might be redundant with a good selector)
            for link in page_links:
                if link_pattern.match(link):
                    all_listing_links.append(link)

            print(f"Found {len(page_links)} potential links on page. Added {len([l for l in page_links if link_pattern.match(l)])} valid links.")
            time.sleep(0.5) # Small polite delay between page loads

    except Exception as e:
        print(f"CRITICAL ERROR during link gathering: {e}")
        # Log traceback if needed
    finally:
        if driver:
            print("Quitting main link-gathering driver.")
            driver.quit()

    # Deduplicate links
    unique_links = sorted(list(set(all_listing_links)))
    print(f"--- Found {len(unique_links)} unique listing links across {config_dict['n_pages']} pages ---")
    return unique_links


# --- Main Execution ---
if __name__ == "__main__":
    start_time = time.time()

    # 1. Gather all links sequentially
    all_links = gather_listing_links(CONFIG)

    property_stats = []
    if all_links:
        # 2. Process links in parallel
        print(f"\n--- Phase 2: Starting Parallel Scraping ({CONFIG['num_workers']} workers) ---")

        # Use partial to fix the config argument for the worker function
        # Pass a copy of CONFIG to avoid potential modification issues if CONFIG were mutable
        worker_func = partial(scrape_single_listing, config_dict=CONFIG.copy())

        try:
            with multiprocessing.Pool(processes=CONFIG['num_workers']) as pool:
                # Use imap_unordered for potentially better memory usage and responsiveness
                results_iterator = pool.imap_unordered(worker_func, all_links)

                count = 0
                for result in results_iterator:
                    count += 1
                    if result: # Only append successful results (worker returns dict)
                        property_stats.append(result)
                    # Simple progress indicator
                    print(f"PROGRESS: Processed {count} / {len(all_links)} listings... (Collected {len(property_stats)} successful)", end='\n')
                print("\nParallel processing finished.") # Newline after progress

        except Exception as e:
            print(f"\nCRITICAL ERROR during parallel processing: {e}")
            # Log traceback if needed

    else:
        print("No links found to process.")

    # 3. Post-Processing - Save results
    print("\n--- Phase 3: Saving Data ---")
    if property_stats:
        try:
            property_stats_df = pd.DataFrame(property_stats)
            current_time_str = time.strftime("%y%m%d_%H%M")
            output_basename = f"{CONFIG['output_dir']}/property_data_{current_time_str}"

            # Ensure output directory exists
            import os
            os.makedirs(CONFIG['output_dir'], exist_ok=True)

            parquet_path = output_basename + ".parquet"
            csv_path = output_basename + ".csv"

            property_stats_df.to_parquet(parquet_path)
            print(f"Saved Parquet file: {parquet_path}")
            property_stats_df.to_csv(csv_path, index=False)
            print(f"Saved CSV file: {csv_path}")

        except Exception as e:
            print(f"Error saving data: {e}")
            # Fallback: Save raw list as pickle
            try:
                pickle_path = f"{CONFIG['output_dir']}/property_stats_fallback_{time.strftime('%y%m%d_%H%M')}.pickle"
                with open(pickle_path, "wb") as fp:
                    pickle.dump(property_stats, fp)
                print(f"Saved raw data fallback as pickle: {pickle_path}")
            except Exception as pe:
                print(f"Failed to save pickle fallback: {pe}")
    else:
        print("No data collected to save.")

    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")
