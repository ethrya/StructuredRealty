from openai import OpenAI
from helpers.openai_key import openai_key
from helpers.chatgpt_helpers import get_chat_gpt_response

import pandas as pd

property_data = pd.read_parquet("outdata/property_data_241215_1913.parquet", engine = "pyarrow")

def run_chatgpt():
    print(openai_key)

client = OpenAI(
    api_key = openai_key
)



base_prompt = "I will pass you  a real estate listing. Return the: strata costs, rates, rental estimate, internal size and external size. Format the response with one line per item and the format \"item: value\". If you are unsure write \"unsure\". If the lising does not include an item write: \"n/a\". Return the data as a json array with the following properties: [strata_costs, rates, rental_estimate, internal_size_sqm, external_size_sqm]. The listing is:"

listings_description = property_data["property_desc_text"]

listing_summary = []

for listing in listings_description[0:3]:
    listing_summary.append(get_chat_gpt_response(base_prompt+listing))