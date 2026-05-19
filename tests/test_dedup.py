"""Tests for pipeline.dedup filter_by_keywords."""

from __future__ import annotations

import pytest

from pipeline.dedup import filter_by_keywords


def test_filter_by_keywords_tags_with_cluster_id():
    jobs = [{"title": "Civil Engineer"}, {"title": "Bartender"}]
    keyword_to_cluster_map = {"civil engineer": "CLU_1", "bartender": "CLU_2"}
    result = filter_by_keywords(jobs, keyword_to_cluster_map)
    assert len(result) == 2
    assert result[0]["cluster"] == "CLU_1"
    assert result[1]["cluster"] == "CLU_2"


def test_filter_by_keywords_drops_non_matching_jobs():
    jobs = [{"title": "Civil Engineer"}, {"title": "Astronaut"}]
    keyword_to_cluster_map = {"civil engineer": "CLU_1"}
    result = filter_by_keywords(jobs, keyword_to_cluster_map)
    assert len(result) == 1
    assert result[0]["title"] == "Civil Engineer"


def test_filter_by_keywords_case_insensitive_title_match():
    jobs = [{"title": "CIVIL ENGINEER"}]
    keyword_to_cluster_map = {"civil engineer": "CLU_1"}
    result = filter_by_keywords(jobs, keyword_to_cluster_map)
    assert len(result) == 1
    assert result[0]["cluster"] == "CLU_1"


def test_filter_by_keywords_empty_map_drops_all():
    jobs = [{"title": "Civil Engineer"}, {"title": "Bartender"}]
    result = filter_by_keywords(jobs, {})
    assert result == []


def test_filter_by_keywords_substring_match():
    """A keyword that is a substring of the title still matches."""
    jobs = [{"title": "Senior Civil Engineer at Acme"}]
    keyword_to_cluster_map = {"civil engineer": "CLU_1"}
    result = filter_by_keywords(jobs, keyword_to_cluster_map)
    assert len(result) == 1
    assert result[0]["cluster"] == "CLU_1"
