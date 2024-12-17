from openai import OpenAI
from helpers.openai_key import openai_key
from helpers.chatgpt_helpers import get_chat_gpt_response

import pandas as pd
import json

property_data = pd.read_parquet("outdata/property_data241216_0752.parquet", engine = "pyarrow")

client = OpenAI(
    api_key = openai_key
)



base_prompt = "I will pass you a real estate listing.\
    Return the: strata costs, rates, rental estimate, internal size and external size.\
    The value should be a number or range of numbers.\
    For the strata costs, include the total of strata, body corporate, admin and sinking fund costs, if they are stated.\
    For the strata costs, rates and rental estimates, include a column with the time period (e.g. week, quarter or year)\
    If you are unsure write \"unsure\". If the lising does not include an item write: \"n/a\".\
    Return the data as a json array with the following properties: [strata_costs, strata_cost_unit, rates, rates_unit,\
        rental_estimate, rental_estimate_unit, internal_size,\
        external_size].\
    The listing is:"

listing_summary = []

#chat_gpt_output = get_chat_gpt_response(base_prompt+listing)


for index, row in property_data.iloc[0:5].iterrows():
    chat_gpt_output = get_chat_gpt_response(base_prompt+row["property_desc_text"])
    listing_summary.append(json.loads(chat_gpt_output))

listing_df  = pd.DataFrame.from_records(listing_summary)

listing_combined = pd.concat([property_data, listing_df], axis = 1)
listing_combined.to_csv("outdata/listing_info.csv")