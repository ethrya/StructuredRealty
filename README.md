# housing_data

The goal of this project is model prices of recently sold properties in an area.

This involves 

1. Getting listings of recently sold properties from domain.com.au
2. Putting the listing descriptions through chatgpt to extract addtiional information, such as interior size and strata costs
3. Fitting a model to the data.

# Project structure
Each of the steps above has a main script that runs the code for that script.

1. **Scraping listings:** `get_domain_data.py` scrapes domain.com.au with given parameters in the script.
2. **Get additional data from description.** `