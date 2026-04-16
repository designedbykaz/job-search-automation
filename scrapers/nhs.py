# nhs.py — scrapes NHS Jobs via the Apify actor
# Actor: azzouzana/apify-scrapers (NHS UK Jobs)
# Returns a list of job dicts with keys: title, employer, location, date, url

from apify_client import ApifyClient
from config.keywords import JOB_KEYWORDS
import os
from dotenv import load_dotenv

load_dotenv()


def scrape_nhs_jobs():
    client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
    results = []

    # TODO: configure actor input with keyword list and run
    # TODO: parse and return results as list of dicts

    return results
