"""
Given a DataFrame with property listing information, get additional information from the property description
"""
from openai import OpenAI

import pandas as pd
import json
import re

from helpers.openai_key import openai_key
from helpers.chatgpt_helpers import get_chat_gpt_response

print("Loading data and setting up")

# load in property data to examine
# This could be created using `get_domain_data.py``
property_data_file = "property_data_250520_0032.parquet"
property_data = pd.read_parquet("outdata/" + property_data_file, engine = "pyarrow")

max_listings = min(10000000, len(property_data))


client = OpenAI(
    api_key = openai_key
)

base_prompt = "I will pass you a real estate listing.\
    From the listing, determine the following measures: strata costs, rates, rental estimate, internal size, external size, type of outdoor space, energy efficiency rating (EER) and year built.\
    For each field, value should be a number. If the listing refers to a range of numbers, use the smallest. Don't include the unit in that field.\
    For the strata costs, include the total of strata, body corporate, admin and sinking fund costs, if they are stated.\
    For the strata costs, rates and rental estimates, include a column with the time period referred to in the listing (e.g. week, quarter or year).\
    If you are unsure or there is no mention of the item set the value to null.\
    The type of outdoor space should be one of: garden, courtyard, balcony, none, unsure. If multiple, pick the first option in the list.\
    Return the data as a json object with the following properties: [strata_costs, strata_cost_unit, rates, rates_unit,\
        rental_estimate, rental_estimate_unit, internal_size, external_size, outdoor_type, EER, year_built].\
    The listing is:"

listing_summary = []

print("Getting info from Chat GPT")

# For each listing get the chatgpt response and save it as a list of json files
for index, row in property_data.iloc[0:max_listings].iterrows():
    if (index + 1) % 10 == 0:
        print("Getting info for listing: " 
              + str(index + 1) + " of " + str(max_listings) 
              + " ("f"{(index+1)/max_listings:.0%}" + ")")
    
    chat_gpt_output = get_chat_gpt_response(client, base_prompt+row["property_desc_text"])
    listing_summary.append(json.loads(chat_gpt_output))

# Create a DataFrame from the list of json arrays
listing_df  = pd.DataFrame.from_records(listing_summary)


output_file_path = "listing_info_" + re.sub("property_data_(\d{6}_\d{4}).parquet", "\g<1>", property_data_file)
listing_combined = pd.concat([property_data, listing_df], axis = 1)
listing_combined.to_csv("outdata/" + output_file_path + ".csv")
listing_combined.to_parquet("outdata/" + output_file_path + ".parquet")