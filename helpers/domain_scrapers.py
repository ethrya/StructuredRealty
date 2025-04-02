# These functions are helpers for the get_domain_data script
# They extract the required elements and are some reusable code.
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import re
import time
from datetime import datetime
from bs4 import BeautifulSoup


# helper to get html data
def get_element_html_by_class(driver, class_name):
    try:
        element_html = driver.find_element(by = By.CLASS_NAME, value = class_name).get_attribute("innerHTML")
    except selenium.common.exceptions.NoSuchElementException:
        element_html = ""
    
    return element_html

def get_element_html_by_testid(driver, data_testid, tag_name):
    try:
        # Define the CSS selector targeting the data-testid attribute
        # Format: tag[attribute='value']
        css_selector = tag_name + "[data-testid='" + data_testid + "']"        
        element_html = driver.find_element(by = By.CSS_SELECTOR, value = css_selector).get_attribute("innerHTML")
    except selenium.common.exceptions.NoSuchElementException:
        element_html = ""
    
    return element_html

# Get data on bed, bath, parking from an element which includes this info
def get_bed_bath_park_data(element):
    try:
        n = re.search("^\d{1}", element.get_attribute("innerHTML")).group()
    except AttributeError:
        n = "0"

    return int(n)


def get_text_from_html_string(html_string):
    soup = BeautifulSoup(html_string, "html.parser")
    text_content_bs = soup.get_text(separator=' ', strip=True)

    return text_content_bs


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

# For a listing_link, navagte to the link and extract key data.
def get_listing_info(driver, listing_link):
    # Navigate to listing
    print("Navigating to listing: " + listing_link)
    driver.get(listing_link)
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='listing-details__button-copy-wrapper']")))
    except selenium.common.exceptions.TimeoutException:
        print("Timed out waiting for the required element to be present.")


    time.sleep(10)

    # Get key listing stats
    address = get_element_html_by_testid(driver, "listing-details__button-copy-wrapper", "div")
    # This is the line with the sale status and price "e.g. SOLD - $600,000"
    sale = get_element_html_by_testid(driver, "listing-details__summary-title", "div")
    sale_method_date = get_element_html_by_testid(driver, "listing-details__listing-tag", "span")
    # This is the element that contains the bed/bath/car status and the dwelling type. We do this because the css 
    #     selectors are reefered to in other places too
    #key_details = driver.find_element(by = By.CSS_SELECTOR, value = "span[data-testid='property-features']")
    element = driver.find_elements(by = By.CSS_SELECTOR, value = "span[data-testid='property-features-text-container']")
    dwelling_type = get_element_html_by_testid(driver, "listing-summary-property-type", "div")

    # There is normally a read more button that hides additional property lising into and needs to be clicked
    try:
        read_more_button_selector = "div[data-testid='listing-details__description-button']"  
        read_more_button = driver.find_element(by = By.CSS_SELECTOR, value = read_more_button_selector)
        read_more_button.click()
        time.sleep(5)
    except selenium.common.exceptions.NoSuchElementException:
        pass

    property_desc = get_element_html_by_class(driver, "css-bq4jj8")

    # Get the elements saved above and tidy into a usable format
    listing_info = {"address": get_text_from_html_string(address),
            "sale_price": re.search("\$[\d\,]+", sale).group(),
            "sale_date": datetime.strptime(re.sub("^Sold (\D+)(\d{1,2}.+20\d{2})$", "\g<2>", sale_method_date),
                                           "%d %b %Y").date(),
            "sale_method": re.sub("^Sold (\D+)(\d{1,2}.+20\d{2}$)", "\g<1>", sale_method_date),
            "dwelling_type": get_text_from_html_string(dwelling_type),
            "n_beds": get_bed_bath_park_data(element[0]),
            "n_bath": get_bed_bath_park_data(element[1]),
            "n_park": get_bed_bath_park_data(element[2]),
            "property_desc_text": get_text_from_html_string(property_desc)
    }

    return listing_info




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
        options.binary_location = config_dict['firefox_path']
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
