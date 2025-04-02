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

# For a listing_link, navagte to the link and extract key data.
def get_listing_info(driver, listing_link):
    # Navigate to listing
    print("Navigating to listing: " + listing_link)
    driver.get(listing_link)
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='']")))
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
