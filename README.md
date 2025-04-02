# Canberra Property Data Scraper & Analyzer

## Description

This project scrapes Canberran sold property listing data (from Domain.com.au) and then uses the OpenAI API (ChatGPT) to extract structured information (such as strata costs, property size, energy efficiency rating, etc.) from the free-text property descriptions provided in the listings. The goal is to create a structured dataset for property analysis.

## Features

* Scrapes sold listings from Domain.com.au based on specified suburbs and search conditions.
* Extracts key details available directly on listing pages (e.g., bedrooms, bathrooms, parking - via helper functions).
* Utilizes the OpenAI API (GPT models) to parse unstructured text descriptions into structured data points (costs, sizes, EER, year built, etc.).
* Implements parallel processing (using Python's `multiprocessing`) for faster scraping of individual listings and/or processing descriptions via the OpenAI API.
* Saves the combined original and extracted data in CSV and Apache Parquet formats.
* Configurable search parameters and settings.
* **(Future)** Includes a property pricing model component (currently under development).

## Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    ```

2.  **Python Environment:**
    * Ensure you have Python installed (developed with Python 3.9+, compatibility with other 3.x versions may vary).

3.  **Install Dependencies:**
    * Install required Python packages using pip:
        ```bash
        pip install -r requirements.txt
        ```

4.  **WebDriver:**
    * Download the appropriate WebDriver for the browser you intend to use (e.g., `geckodriver` for Firefox, `chromedriver` for Chrome).
    * Ensure the WebDriver executable is either in your system's PATH or specify the full path to it in the configuration (see below).

5.  **OpenAI API Key:**
    * Obtain an API key from OpenAI: [https://platform.openai.com/](https://platform.openai.com/)
    * add the key as a variable `openai_key` in a helpers/openai_key.api folder

## Configuration

Scraping settings can be configured by editing the `CONFIG` dictionary in `your_main_script.py`.

Key configurable parameters include:

* `suburbs`: Comma-separated list of suburbs formatted following the domain.com.au url formatting (e.g., `campbell-act-2612,reid-act-2612`).
* `conditions`: Additional URL query parameters for filtering (e.g., `&bedrooms=2&excludepricewithheld=1`).
* `n_pages`: Number of search result pages to scrape per run.
* `geckodriver_path` / `chromedriver_path`: Full path to your WebDriver executable (if not in system PATH).
* `firefox_path` / `chrome_path`: Full path to your browser binary (if not detected automatically).
* `output_dir`: Directory where output files (CSV, Parquet) will be saved (e.g., `outdata/`).
* `num_workers`: Number of parallel processes to use for scraping/processing.
* `max_listings`: (If applicable) Maximum number of listings to process via OpenAI API per run.

## Usage

1.  **Configure:** Ensure all necessary settings are configured as described above.
2.  **Run the Scraper:**
    * `python get_domain_data.py`
    * This script will typically handle fetching data from Domain.com.au and saving intermediate results.
3.  **Run the OpenAI Processor:**
    * `python chatgpt_summarise.py`]
    * This script reads the scraped data, sends descriptions to OpenAI, parses the results, and saves the final combined dataset.

## Output

The primary outputs are saved in the configured `output_dir` (default: `outdata/`):

* **`property_data_YYMMDD_HHMM.parquet`**: Apache Parquet file containing the combined data (original scraped info + structured data extracted by OpenAI). Parquet is efficient for larger datasets.
* **`property_data_YYMMDD_HHMM.csv`**: CSV file containing the same combined data for easier viewing or use in spreadsheet software.

The columns will include original scraped data (URL, description, bed/bath/park) and the fields extracted by OpenAI (strata\_costs, strata\_cost\_unit, rates, rates\_unit, rental\_estimate, rental\_estimate\_unit, internal\_size, external\_size, EER, year\_built).

## Dependencies

Install using: `pip install -r requirements.txt`

## Future Work

* **Pricing Model:** Integrate the property pricing model component (currently under development).
* **Error Handling:** Enhance robustness with more granular error handling and logging.
* **Configuration:** Improve configuration management (e.g., fully implement `argparse` or YAML loading).
* **Database Integration:** Add option to save results directly to a database.

## License

Licensed under the GNU Affero General Public License v3.0 - see the LICENSE file for details.
