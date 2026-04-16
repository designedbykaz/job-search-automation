# totaljobs.py — scrapes Totaljobs via the Apify actor
# Actor: ecomscrape/totaljobs-jobs-search-scraper
# Returns a list of job dicts with keys: title, employer, location, date, url

from apify_client import ApifyClient
from config.keywords import JOB_KEYWORDS
import os
from dotenv import load_dotenv

load_dotenv()


def scrape_totaljobs():
    client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
    results = []

    # TODO: configure actor input with keyword list and run
    # TODO: parse and return results as list of dicts

    return results
