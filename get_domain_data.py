"""
Get real estate listing data for a set of paramaters and locations.
Selenium is used to scrape lisings from domain.com.au and the key details (e.g. sale dates, 
prices, number of beedrooms) and property description are recorded.
"""

import re
from bs4 import BeautifulSoup

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
from pyarrow import Table
from pyarrow import parquet as pq
import pickle
import time

from helpers.domain_scrapers import get_bed_bath_park_data, get_element_html_by_class, get_listing_info

# Parameters to set
# Set which suburbs you would like to review in the format used by domain.
# This format is suburb-state-postcode. Each suburb is separated by a space
suburbs = "campbell-act-2612,reid-act-2612,braddon-act-2612,ainslie-act-2602,\
dickson-act-2602,lyneham-act-2602,o-connor-act-2602,\
turner-act-2612,downer-act-2602,watson-act-2602"
# Add in any additional conditions, such as the number of bedrooms or bathrooms.
# This may only work if excludepricewithheld-=1
conditions = "&bedrooms=2&excludepricewithheld=1"

domain_base_page = "https://www.domain.com.au/sold-listings/?suburb=" + suburbs + conditions +"&page="

# How many pages of listings do you want to review?
# One page here includes links to many individual listings
n_pages = 1


# Get a list of pages
domain_pages = [domain_base_page + str(i+1) for i in range(n_pages)]

current_time = time.strftime("%y%m%d_%H%M")


# Setup Selenium driver

print("Initialising")

# This needs to point to your selenium driver's location
service = Service(executable_path = '/usr/local/bin/geckodriver')

options = webdriver.FirefoxOptions()
# This needs to point to the firefox location.
options.binary_location = "/Applications/Firefox.app/Contents/MacOS/firefox"
options.page_load_strategy = 'eager'
driver = webdriver.Firefox(service=service, options=options)
driver.set_page_load_timeout(15)


# Extract data for each page of listings
property_stats = []

try:

    for base_page in domain_pages:

        print("Navigating to domain: " + base_page)
        # Sometimes, domain.com.au takes a long time to fully load, but the information is there.
        # This allows the code to continue after it times out.
        
        driver.get(base_page)
        try:
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='listing-card-lazy-image']")))
        except selenium.common.exceptions.TimeoutException:
            print("Timed out waiting for the required element to be present.")

        time.sleep(5)

        # Get elements with a link, then extract just the links
        elems_with_links = driver.find_elements(by=By.XPATH, value="//a[@href]")

        links = [elem.get_attribute("href") for elem in elems_with_links]

        # Only include links that match the following pattern, as they are sold listings
        pattern = r"https://www\.domain\.com\.au/\w+-.+-act-\d{4}-\d{10}"

        listing_links = [link for link in links if  bool(re.match(pattern, link))]
        # Get rid of duplicate links
        listing_links = list(set(listing_links))

        # Not get data for each sold listing
        for link in listing_links:
            try:
                listing_info = get_listing_info(driver, link)
                property_stats.append(listing_info)
            except selenium.common.exceptions.NoSuchElementException:
                print("Something with wrong with: " & link)
        # Save in each loop so data is not lost if there is an error
        with open("outdata/property_intermediate_bin.pickle", "wb") as fp:
            pickle.dump(property_stats, fp)
        
finally:
    driver.quit()

property_stats_df = pd.DataFrame(property_stats)

property_stats_df.to_parquet("outdata/property_data" + current_time + ".parquet")
property_stats_df.to_csv("outdata/property_data_" + current_time + ".csv")