import os

import re
from bs4 import BeautifulSoup

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

import pandas as pd
from pyarrow import Table
from pyarrow import parquet as pq
import pickle
import time
import datetime
from datetime import datetime

from helpers.domain_scrapers import get_bed_bath_park_data, get_element_html_by_class, get_listing_info


current_time = time.strftime("%y%m%d_%H%M")

suburbs = "campbell-act-2612,reid-act-2612,braddon-act-2612,ainslie-act-2602,\
    dickson-act-2602,lyneham-act-2602,o-connor-act-2602,\
    turner-act-2612,downer-act-2602,watson-act-2602"
conditions = "&bedrooms=2&excludepricewithheld=1"
domain_base_page = "https://www.domain.com.au/sold-listings/?suburb=" + suburbs + conditions +"&page="

n_pages = 20

domain_pages = [domain_base_page + str(i+1) for i in range(n_pages)]


print("Initialising")

service = Service(executable_path = '/usr/local/bin/geckodriver')

options = webdriver.FirefoxOptions()
options.binary_location = "/Applications/Firefox.app/Contents/MacOS/firefox"
driver = webdriver.Firefox(service=service, options=options)
driver.set_page_load_timeout(15)

property_stats = []

for base_page in domain_pages:

    print("Navigating to domain: " + base_page)
    try:
        driver.get(base_page)
    except selenium.common.exceptions.TimeoutException:
        print("Force timed out... continuing")

    time.sleep(5)

    # Get elements with a link, then extract just the links
    elems_with_links = driver.find_elements(by=By.XPATH, value="//a[@href]")

    links = [elem.get_attribute("href") for elem in elems_with_links]

    # Only include links that match the following pattern, as they are sold listings
    pattern = r"https://www\.domain\.com\.au/\d+-.+-act-\d{4}-\d{10}"

    listing_links = [link for link in links if  bool(re.match(pattern, link))]
    # Get rid of duplicate links
    listing_links = list(set(listing_links))

    for link in listing_links:
        try:
            listing_info = get_listing_info(driver, link)
            property_stats.append(listing_info)
        except selenium.common.exceptions.NoSuchElementException:
            print("Something with wrong with: " & link)

    with open("outdata/property_intermediate_bin.pickle", "wb") as fp:
        pickle.dump(property_stats, fp)
    

driver.quit()

property_stats_df = pd.DataFrame(property_stats)

property_stats_df.to_parquet("outdata/property_data" + current_time + ".parquet")
property_stats_df.to_csv("outdata/property_data_" + current_time + ".csv")