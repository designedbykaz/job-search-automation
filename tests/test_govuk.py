"""Tests for scrapers.govuk scrape_govuk_jobs input validation."""

from __future__ import annotations

import pytest

from scrapers.govuk import scrape_govuk_jobs


def test_scrape_govuk_raises_without_keywords():
    with pytest.raises(ValueError):
        scrape_govuk_jobs()


def test_scrape_govuk_raises_with_none_keywords():
    with pytest.raises(ValueError):
        scrape_govuk_jobs(keywords=None)


def test_scrape_govuk_raises_with_empty_keywords():
    with pytest.raises(ValueError):
        scrape_govuk_jobs(keywords=[])
