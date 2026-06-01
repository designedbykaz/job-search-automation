"""Phase 1 data-layer checks for the CV tailoring rework.

Covers the resolver (tier selection, the substantial test, the leadership
cross-section quirk, facts travelling from the floor, missing identities) and
the content index builder. Tests run against small inline fixtures so they are
deterministic and independent of the gitignored personal content; one cloner-
safe smoke test exercises the committed example files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline import cv_sources

# A body line comfortably over the 120-char substantial threshold.
LONG = (
    "This is a deliberately long reservoir line written so that a single "
    "entry clears the substantial threshold on its own during testing."
)


@pytest.fixture
def master_profile() -> dict:
    return {
        "cv": {
            "education": {
                "leeds": [LONG, "Modules in solid mechanics and HCI."],
            },
            "projects": {
                "pill_pod": [LONG, "Applied EAST and COM-B behavioural models."],
            },
            "experience": {
                "siffa": [LONG, "Sole designer on the festival deliverables."],
                # product_design_society lives under experience in master_profile,
                # even though the floor files it under leadership.
                "product_design_society": [LONG, "Chaired committee meetings."],
                # Thin: below the threshold, should fall through to the floor.
                "ashtar": ["Bar staff."],
            },
        }
    }


@pytest.fixture
def base() -> dict:
    return {
        "education": [
            {
                "id": "leeds",
                "institution": "University of Leeds",
                "subline": "School of Mechanical Engineering",
                "dates": "2022 - 2025",
                "qualification": "BSc Product Design (2:1)",
                "details": ["A floor education detail line for the University of Leeds entry."],
            }
        ],
        "projects": [
            {
                "id": "pill_pod",
                "title": "PillPod",
                "stack": "SolidWorks, Arduino, Figma",
                "bullets": ["A floor bullet describing the PillPod final year project."],
            }
        ],
        "leadership": [
            {
                "id": "product_design_society",
                "role": "President",
                "org": "Product Design Society",
                "dates": "2024 - 2025",
                "bullets": ["A floor bullet about leading the Product Design Society."],
            }
        ],
        "experience": [
            {
                "id": "siffa",
                "role": "Freelance Digital Designer",
                "company": "SIFFA Media",
                "dates": "Oct - Nov 2025",
                "bullets": ["A floor bullet about the SIFFA festival design work."],
            },
            {
                "id": "ashtar",
                "role": "Bar Staff",
                "company": "Ashtar",
                "dates": "2018 - 2021",
                "bullets": [
                    "A reasonably long floor bullet about sustained bar service that "
                    "comfortably exceeds the substantial threshold for this test."
                ],
            },
            {
                # Present in the floor but absent from master_profile entirely.
                "id": "halewood",
                "role": "Intern",
                "company": "Halewood International",
                "dates": "2017",
                "bullets": [
                    "A floor-only bullet about the Halewood marketing internship, with "
                    "no matching master_profile entry anywhere in the fixtures."
                ],
            },
        ],
    }


# --- the substantial test ------------------------------------------------


def test_substantial_threshold_boundary():
    assert cv_sources._is_substantial(["x" * (cv_sources.SUBSTANTIAL_MIN_CHARS - 1)]) is False
    assert cv_sources._is_substantial(["x" * cv_sources.SUBSTANTIAL_MIN_CHARS]) is True
    assert cv_sources._is_substantial([]) is False
    assert cv_sources._is_substantial(["", "   "]) is False


# --- resolver tier selection --------------------------------------------


def test_resolve_prefers_master_profile_when_substantial(master_profile, base):
    r = cv_sources.resolve_item("siffa", "experience", master_profile=master_profile, base=base)
    assert r["tier"] == cv_sources.TIER_MASTER_PROFILE
    assert r["substantial"] is True
    assert r["body"][0] == LONG


def test_resolve_falls_back_to_floor_when_master_profile_missing(master_profile, base):
    r = cv_sources.resolve_item("halewood", "experience", master_profile=master_profile, base=base)
    assert r["tier"] == cv_sources.TIER_BASE
    assert r["substantial"] is True
    assert "Halewood" in r["body"][0]


def test_resolve_skips_thin_master_profile(master_profile, base):
    # ashtar has a one-line, sub-threshold master_profile body; the richer
    # floor bullet should win instead.
    r = cv_sources.resolve_item("ashtar", "experience", master_profile=master_profile, base=base)
    assert r["tier"] == cv_sources.TIER_BASE
    assert r["substantial"] is True


def test_resolve_leadership_uses_experience_pool(master_profile, base):
    r = cv_sources.resolve_item(
        "product_design_society", "leadership", master_profile=master_profile, base=base
    )
    # Body comes from the master_profile experience pool...
    assert r["tier"] == cv_sources.TIER_MASTER_PROFILE
    assert r["body"][0] == LONG
    # ...but facts come from the floor's leadership item.
    assert r["facts"]["role"] == "President"
    assert r["facts"]["org"] == "Product Design Society"


def test_resolve_unknown_identity_returns_none_tier(master_profile, base):
    r = cv_sources.resolve_item("nope", "experience", master_profile=master_profile, base=base)
    assert r["tier"] == cv_sources.TIER_NONE
    assert r["body"] == []
    assert r["facts"] == {"role": "", "company": "", "dates": ""}


def test_resolve_unknown_section_raises(master_profile, base):
    with pytest.raises(ValueError):
        cv_sources.resolve_item("siffa", "skills_columns", master_profile=master_profile, base=base)


def test_facts_travel_unchanged_from_floor(master_profile, base):
    r = cv_sources.resolve_item("siffa", "experience", master_profile=master_profile, base=base)
    assert r["facts"] == {
        "role": "Freelance Digital Designer",
        "company": "SIFFA Media",
        "dates": "Oct - Nov 2025",
    }


def test_floor_body_is_the_verified_fallback(master_profile, base):
    # body is the richer master_profile source; floor_body is the floor's bullets.
    r = cv_sources.resolve_item("siffa", "experience", master_profile=master_profile, base=base)
    assert r["tier"] == cv_sources.TIER_MASTER_PROFILE
    assert r["body"][0] == LONG
    assert r["floor_body"] == ["A floor bullet about the SIFFA festival design work."]


# --- vault tier ----------------------------------------------------------


def test_resolve_uses_vault_when_substantial(master_profile, base, tmp_path):
    vault = tmp_path / cv_sources.VAULT_DIRNAME
    vault.mkdir()
    (vault / "siffa.md").write_text(
        "# SIFFA\n\n- " + LONG + "\n- A second vault line about the festival.\n",
        encoding="utf-8",
    )
    r = cv_sources.resolve_item(
        "siffa", "experience", master_profile=master_profile, base=base, vault_dir=vault
    )
    assert r["tier"] == cv_sources.TIER_VAULT
    assert r["body"][0] == LONG  # heading dropped, bullet marker stripped
    assert all(not line.startswith("#") for line in r["body"])


def test_resolve_ignores_thin_vault(master_profile, base, tmp_path):
    vault = tmp_path / cv_sources.VAULT_DIRNAME
    vault.mkdir()
    (vault / "siffa.md").write_text("# SIFFA\n\n- TODO\n", encoding="utf-8")
    r = cv_sources.resolve_item(
        "siffa", "experience", master_profile=master_profile, base=base, vault_dir=vault
    )
    # Thin vault is skipped; master_profile wins.
    assert r["tier"] == cv_sources.TIER_MASTER_PROFILE


# --- content index -------------------------------------------------------


def test_build_content_index_one_record_per_floor_item(master_profile, base):
    index = cv_sources.build_content_index(master_profile=master_profile, base=base)
    # 1 education + 1 project + 1 leadership + 3 experience.
    assert len(index) == 6
    by_id = {r["identity"]: r for r in index}
    assert set(by_id) == {"leeds", "pill_pod", "product_design_society", "siffa", "ashtar", "halewood"}

    for record in index:
        assert set(record) == {"identity", "section", "title", "first_line", "tier", "substantial"}

    assert by_id["product_design_society"]["section"] == "leadership"
    assert by_id["product_design_society"]["title"] == "President, Product Design Society"
    assert by_id["leeds"]["title"] == "University of Leeds"
    assert by_id["pill_pod"]["title"] == "PillPod"


def test_index_tiers_reflect_resolution(master_profile, base):
    by_id = {r["identity"]: r for r in cv_sources.build_content_index(
        master_profile=master_profile, base=base
    )}
    assert by_id["siffa"]["tier"] == cv_sources.TIER_MASTER_PROFILE
    assert by_id["halewood"]["tier"] == cv_sources.TIER_BASE
    assert by_id["ashtar"]["tier"] == cv_sources.TIER_BASE


def test_index_first_line_comes_from_resolved_body(master_profile, base):
    by_id = {r["identity"]: r for r in cv_sources.build_content_index(
        master_profile=master_profile, base=base
    )}
    assert by_id["siffa"]["first_line"] == LONG
    assert "Halewood" in by_id["halewood"]["first_line"]


# --- cloner-safe smoke test against the committed example files ----------


def test_example_files_resolve_without_error():
    content_dir = Path(__file__).resolve().parents[1] / "content"
    with (content_dir / "master_profile.example.json").open(encoding="utf-8") as f:
        master_profile = json.load(f)
    with (content_dir / "base_cv_content.example.json").open(encoding="utf-8") as f:
        base = json.load(f)

    index = cv_sources.build_content_index(master_profile=master_profile, base=base)
    # Every example floor item carries an id and appears exactly once.
    assert {r["identity"] for r in index} == {
        "primary_institution",
        "project_1",
        "leadership_role_1",
        "employer_1",
    }
    for record in index:
        assert record["tier"] in {
            cv_sources.TIER_VAULT,
            cv_sources.TIER_MASTER_PROFILE,
            cv_sources.TIER_BASE,
            cv_sources.TIER_NONE,
        }
