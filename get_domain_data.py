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
    "n_pages": 40, # How many search results pages to scrape
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
                    print(f"PROGRESS: Processed {count} / {len(all_links)} listings... (Collected {len(property_stats)} successful)", end='\r')
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
