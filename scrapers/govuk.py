# govuk.py — scrapes GOV.UK Jobs (https://www.jobs.gov.uk) per keyword

import re
import time
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from config.keywords import JOB_KEYWORDS

load_dotenv()

BASE_URL = "https://findajob.dwp.gov.uk"
SEARCH_URL = "https://findajob.dwp.gov.uk/search"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_DELAY = 1.5  # seconds between requests


def can_fetch(url):
    try:
        robots_url = BASE_URL + "/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch("*", url)
        if not allowed:
            print(f"Warning: robots.txt disallows {url}. Proceeding anyway at low volume.")
        return True
    except Exception as e:
        print(f"Warning: could not fetch robots.txt ({e}). Defaulting to allowed.")
        return True


def get_job_description(job_url, session):
    empty = {"description": "", "closing_date": "", "contact_info": ""}
    try:
        time.sleep(REQUEST_DELAY)
        response = session.get(job_url, timeout=10)
        if response.status_code != 200:
            return empty
        soup = BeautifulSoup(response.text, "html.parser")
        desc = soup.select_one("div#job-description")
        if not desc:
            desc = soup.select_one("main")
        description = re.sub(r"\s+", " ", desc.get_text(strip=True)) if desc else ""

        # Extract closing date
        closing_date = ""
        page_text = soup.get_text(separator=" ")
        closing_match = re.search(
            r'(?:closing date|apply by|deadline)[^\d]{0,30}(\d{1,2}[\s/\-]\w+[\s/\-]\d{2,4}|\d{1,2}/\d{1,2}/\d{2,4})',
            page_text,
            re.IGNORECASE,
        )
        if closing_match:
            closing_date = closing_match.group(1).strip()

        # Extract contact info
        contact_info = ""
        email_match = re.search(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_text
        )
        if email_match:
            contact_info = email_match.group(0)
        else:
            phone_match = re.search(r'(\+44|0)[0-9\s]{9,12}', page_text)
            if phone_match:
                contact_info = phone_match.group(0).strip()

        return {"description": description, "closing_date": closing_date, "contact_info": contact_info}
    except Exception:
        return empty


def _text_or_empty(el):
    if el is None:
        return ""
    return el.get_text(separator=" ", strip=True)


def _extract_listing_fields(listing_el, base_for_relative):
    """
    Extract title, employer, location, date, url from one result row element.
    TODO: Confirm markup — selectors are placeholders for GOV.UK Jobs HTML.
    """
    title = ""
    employer = ""
    location = ""
    date_str = ""
    url = ""

    # TODO: Replace with verified link/title selector (e.g. h2 a, a.job-title).
    link = listing_el.select_one("a[href]")
    if link and link.get("href"):
        href = link["href"].strip()
        if href.startswith("http"):
            url = href
        else:
            url = urljoin(base_for_relative, href)
        title = _text_or_empty(link)

    # TODO: Confirm class names / structure for employer, location, posted date.
    emp_el = listing_el.select_one(".employer, [class*='employer']")  # placeholder
    employer = _text_or_empty(emp_el)

    loc_el = listing_el.select_one(".location, [class*='location']")  # placeholder
    location = _text_or_empty(loc_el)

    date_el = listing_el.select_one(
        "time, .date, [class*='date'], [class*='posted']"
    )  # placeholder
    date_str = _text_or_empty(date_el)
    if not date_str and date_el and date_el.get("datetime"):
        date_str = date_el.get("datetime", "").strip()

    return title, employer, location, date_str, url


def scrape_govuk_jobs():
    """
    Search GOV.UK Jobs for each JOB_KEYWORDS entry; return list of job dicts.
    Keys: title, employer, location, date, url, description, source.
    """
    results = []

    if not can_fetch(SEARCH_URL):
        print("Warning: robots.txt disallows fetching GOV.UK Jobs search. Skipping.")
        return results

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    for keyword in JOB_KEYWORDS:
        params = {"q": keyword}
        print(f"Searching GOV.UK Jobs for: {keyword}")

        try:
            resp = session.get(SEARCH_URL, params=params, timeout=30)
        except Exception as exc:
            print(f"Warning: request failed for keyword {keyword!r}: {exc}")
            time.sleep(REQUEST_DELAY)
            continue

        time.sleep(REQUEST_DELAY)

        if resp.status_code != 200:
            print(
                f"Warning: search returned status {resp.status_code} for keyword {keyword!r}"
            )
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.search-result")

        for card in cards:
            try:
                title_tag = card.select_one("h3.govuk-heading-s a.govuk-link")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                relative_url = title_tag.get("href", "")
                url = relative_url if relative_url.startswith("http") else BASE_URL + relative_url

                detail_items = card.select("ul.govuk-list.search-result-details li")
                date = detail_items[0].get_text(strip=True) if len(detail_items) > 0 else ""

                employer = ""
                location = ""
                if len(detail_items) > 1:
                    strong = detail_items[1].find("strong")
                    employer = strong.get_text(strip=True) if strong else ""
                    span = detail_items[1].find("span")
                    location = span.get_text(strip=True) if span else ""

                desc_tag = card.select_one("p.govuk-body.search-result-description")
                short_desc = desc_tag.get_text(strip=True) if desc_tag else ""

                detail = get_job_description(url, session)
                description = detail["description"] if detail["description"] else short_desc
                closing_date = detail["closing_date"]
                contact_info = detail["contact_info"]

                results.append(
                    {
                        "title": title,
                        "employer": employer,
                        "location": location,
                        "date": date,
                        "url": url,
                        "description": description,
                        "closing_date": closing_date,
                        "contact_info": contact_info,
                        "source": "govuk",
                    }
                )

            except Exception as e:
                print(f"Warning: failed to parse a job card: {e}")
                continue

    return results
