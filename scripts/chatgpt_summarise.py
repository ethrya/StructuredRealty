from openai import OpenAI
from helpers.openai_key import openai_key
from helpers.chatgpt_helpers import get_chat_gpt_response

def run_chatgpt():
    print(openai_key)

client = OpenAI(
    api_key = openai_key
)

base_prompt = "I will pass you  a real estate listing. Return the: strata costs, rates, rental estimate, internal size and external size. Format the response with one line per item and the format \"item: value\". If you are unsure write \"unsure\". If the lising does not include an item write: \"n/a\".  The listing is:"

listing = "Property Description Investors dream! Located in the highly sought-after suburb of O\'Connor, this 1-bedroom apartment boasts a prime location. The bedroom is bathed in natural light and offers direct access to the balcony, which provides delightful tree-lined views of the nearby parklands. A built-in wardrobe with sliding mirrored doors offers plenty of storage space. Step out onto the private balcony, a sunlit oasis perfect for enjoying a morning coffee or unwinding in an indoor-outdoor setting. The apartment also includes a bathroom with a European laundry, a convenient study nook, and a split system air conditioning unit for year-round comfort. It is nestled within a quiet complex, providing a tranquil living environment. The location adds even more appeal. Positioned in the heart of Canberra's Inner North, it is within walking distance to the ANU, Braddon, Playing Fields, and Canberra City. Moreover, its central location ensures easy access to public transport, making commuting a breeze. Features: Boutique complexInvestors dream Light-filled living with north-west aspectReverse cycle split systemGas hot waterSMEG kitchen appliancesEssentials: EER: 6Rates: $2,094.Expected Rental return: $430.00 to $460.00 per week.Airbnb (guested) $595 weekly approx"

get_chat_gpt_response(base_prompt+listing)