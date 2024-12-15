import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

import re
import time
from bs4 import BeautifulSoup


def get_element_html_by_class(driver, class_name):
    return driver.find_element(by = By.CLASS_NAME, value = class_name).get_attribute("innerHTML")

def get_bed_bath_park_data(element):
    try:
        n = re.search("^\d{1}", element.get_attribute("innerHTML")).group()
    except AttributeError:
        n = "0"

    return n

def get_listing_info(driver, listing_link):
    # Navigate to listing
    print("Navigating to listing: " + listing_link)
    try: 
        driver.get(listing_link)
    except selenium.common.exceptions.TimeoutException:
        print("Force timed out... continuing")

    time.sleep(10)

    # Get key listing stats
    address = get_element_html_by_class(driver, "css-164r41r")
    sale = get_element_html_by_class(driver, "css-twgrok")
    sale_method_date = get_element_html_by_class(driver, "css-h9g9i3")
    key_details = driver.find_element(by = By.CLASS_NAME, value = "css-1dtnjt5")
    element = key_details.find_elements(by = By.CLASS_NAME, value = "css-lvv8is")
    dwelling_type = key_details.find_element(by = By.CLASS_NAME, value="css-in3yi3")

    # There is a read more button that hides additional property lising into and needs to be clicked
    read_more_button = driver.find_element(by = By.CLASS_NAME, value = "css-1pn4141")
    read_more_button.click()
    time.sleep(5)

    property_desc = get_element_html_by_class(driver, "css-bq4jj8")

    # Get the elements saved above and tidy into a usable format
    listing_info = {"address": address,
            "sale_price": re.search("\$[\d\,]+", sale).group(),
            "sale_date": re.sub("^Sold by (\D+)(\d{1,2}.+20\d{2})$", "\g<2>", sale_method_date),
            "sale_method": re.sub("^Sold by (\D+)(\d{1,2}.+20\d{2}$)", "\g<1>", sale_method_date),
            "dwelling_type": dwelling_type.get_attribute("innerHTML"),
            "n_beds": re.search("^\d{1}", element[0].get_attribute("innerHTML")).group(),
            "n_bath": re.search("^\d{1}", element[1].get_attribute("innerHTML")).group(),
            "n_park": re.search("^\d{1}", element[2].get_attribute("innerHTML")).group(),
            "property_desc_text": BeautifulSoup(property_desc, "lxml").text
    }

    return listing_info
