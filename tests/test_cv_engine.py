"""Phase 2 checks for the three-call tailoring engine.

The Claude call is injected, so every test runs offline with canned responses.
Coverage: each step parses its contract; the orchestrator assembles tailored
items with floor-grounded facts; unknown selected identities are dropped;
missing bullets fall back to the floor body; the merge keeps floor values for
anything the model did not produce; a parse failure raises EngineParseError.
"""

from __future__ import annotations

import json

import pytest

from pipeline import cv_engine

# --- inline source fixtures (no dependence on personal content) ----------

LONG = (
    "A deliberately long reservoir line written so a single entry clears the "
    "substantial threshold during testing of the tailoring engine."
)


@pytest.fixture
def master_profile() -> dict:
    return {
        "cv": {
            "personal_profile": ["Product design graduate."],
            "personal_motivations": ["Drawn to human-centred work."],
            "soft_skills": ["Adaptable across environments."],
            "technical_skills": {"cad": ["SolidWorks"], "ui_ux": ["Figma"]},
            "certifications": ["UX cert."],
            "languages": ["English (Native)"],
            "projects": {"pill_pod": [LONG, "Applied COM-B."]},
            "experience": {
                "siffa": [LONG, "Sole designer on the festival."],
                "product_design_society": [LONG, "Chaired meetings."],
            },
        }
    }


@pytest.fixture
def base() -> dict:
    return {
        "identity": {"name": "Test Person", "title": "Grad", "email": "a@b.c",
                     "location": "", "phone": "", "linkedin": ""},
        "objective": "Floor objective.",
        "education": [
            {"id": "leeds", "institution": "University of Leeds", "subline": "",
             "dates": "2022 - 2025", "qualification": "BSc", "details": ["Floor edu detail."]}
        ],
        "certifications": ["Floor cert."],
        "projects": [
            {"id": "pill_pod", "title": "PillPod", "stack": "Arduino",
             "bullets": ["Floor PillPod bullet."]}
        ],
        "leadership": [
            {"id": "product_design_society", "role": "President",
             "org": "Product Design Society", "dates": "2024 - 2025",
             "bullets": ["Floor leadership bullet."]}
        ],
        "experience": [
            {"id": "siffa", "role": "Freelance Digital Designer", "company": "SIFFA Media",
             "dates": "Oct - Nov 2025", "bullets": ["Floor SIFFA bullet."]},
            {"id": "gymfluence", "role": "Online Campaign Manager", "company": "Gymfluence UK",
             "dates": "2021 - 2022", "bullets": ["Floor Gymfluence bullet."]},
        ],
        "skills_columns": [{"heading": "Floor Skills", "bullets": ["Floor skill."]}],
        "skill_tags": [],
        "languages": ["English (Native)"],
    }


# --- a caller that returns queued responses in call order ----------------


class SequenceCaller:
    def __init__(self, responses):
        self._responses = list(responses)
        self.prompts = []

    def __call__(self, prompt, *, max_tokens):
        self.prompts.append(prompt)
        return self._responses.pop(0)


STEP1 = {
    "jd_profile": {"hard_requirements": ["design"], "responsibilities": [],
                   "seniority": "junior", "keywords": ["figma"]},
    "rubric": [{"criterion": "visual design", "weight": 5, "evidence_type": "portfolio work"}],
}

STEP2 = {
    "selection": {
        "experience": [{"identity": "siffa", "rationale": "festival design"}],
        "projects": [{"identity": "pill_pod", "rationale": "device design"}],
        "leadership": [{"identity": "product_design_society", "rationale": "led society"}],
    },
    "gaps": [{"criterion": "agency experience", "note": "no agency role in history"}],
}

STEP3 = {
    "objective": "Tailored objective for this role.",
    "bullets": {
        "siffa": ["Designed festival visual assets."],
        "pill_pod": ["Built an IoT medication device."],
        "product_design_society": ["Led the product design society."],
    },
    "skills_columns": [{"heading": "Design", "bullets": ["Figma", "SolidWorks"]}],
    "skill_tags": ["Figma", "SolidWorks"],
}


def _engine(base, master_profile, responses, template_id="full"):
    caller = SequenceCaller([json.dumps(r) for r in responses])
    cv, report = cv_engine.run_engine(
        {"title": "Junior Designer", "employer": "Acme", "description": "Design things."},
        base=base, master_profile=master_profile, template_id=template_id, caller=caller,
    )
    return cv, report, caller


# --- step parsing --------------------------------------------------------


def test_each_step_parses_its_contract(base, master_profile):
    from pipeline.manifest import load_manifest

    m = load_manifest("full")
    c1 = SequenceCaller([json.dumps(STEP1)])
    assert cv_engine.run_step1({"title": "x", "employer": "", "description": ""}, m, c1)["rubric"]
    c2 = SequenceCaller([json.dumps(STEP2)])
    assert "selection" in cv_engine.run_step2(STEP1, [], m, c2)
    c3 = SequenceCaller([json.dumps(STEP3)])
    assert cv_engine.run_step3(STEP1, {}, {}, {}, m, c3)["objective"]


def test_parse_failure_raises_engine_parse_error(base, master_profile):
    caller = SequenceCaller(["this is not json"])
    with pytest.raises(cv_engine.EngineParseError) as exc:
        cv_engine.run_engine(
            {"title": "x", "employer": "", "description": ""},
            base=base, master_profile=master_profile, template_id="full", caller=caller,
        )
    assert exc.value.step == "analysis"
    assert exc.value.raw == "this is not json"


# --- orchestration -------------------------------------------------------


def test_engine_assembles_items_with_floor_facts(base, master_profile):
    cv, report, _ = _engine(base, master_profile, [STEP1, STEP2, STEP3])

    siffa = next(e for e in cv["experience"] if e["id"] == "siffa")
    # Facts come from the floor, verbatim.
    assert siffa["role"] == "Freelance Digital Designer"
    assert siffa["company"] == "SIFFA Media"
    assert siffa["dates"] == "Oct - Nov 2025"
    # Bullets come from the model.
    assert siffa["bullets"] == ["Designed festival visual assets."]

    assert cv["objective"] == "Tailored objective for this role."
    assert cv["projects"][0]["title"] == "PillPod"
    assert cv["leadership"][0]["role"] == "President"
    assert cv["skills_columns"][0]["heading"] == "Design"


def test_engine_uses_only_selected_experience(base, master_profile):
    # gymfluence is in the floor but not selected; it must not appear.
    cv, _, _ = _engine(base, master_profile, [STEP1, STEP2, STEP3])
    ids = [e["id"] for e in cv["experience"]]
    assert ids == ["siffa"]
    assert "gymfluence" not in ids


def test_engine_drops_unknown_selected_identity(base, master_profile):
    step2 = json.loads(json.dumps(STEP2))
    step2["selection"]["experience"].append({"identity": "ghost_job", "rationale": "made up"})
    cv, report, _ = _engine(base, master_profile, [STEP1, step2, STEP3])
    ids = [e["id"] for e in cv["experience"]]
    assert "ghost_job" not in ids
    assert "ghost_job" not in json.dumps(report["selection"])


def test_engine_falls_back_to_floor_bullets_when_missing(base, master_profile):
    step3 = json.loads(json.dumps(STEP3))
    del step3["bullets"]["siffa"]  # model omitted bullets for siffa
    cv, _, _ = _engine(base, master_profile, [STEP1, STEP2, step3])
    siffa = next(e for e in cv["experience"] if e["id"] == "siffa")
    assert siffa["bullets"] == ["Floor SIFFA bullet."]


def test_merge_keeps_floor_objective_when_blank(base, master_profile):
    step3 = json.loads(json.dumps(STEP3))
    step3["objective"] = ""
    cv, _, _ = _engine(base, master_profile, [STEP1, STEP2, step3])
    assert cv["objective"] == "Floor objective."


def test_mechanical_tiers_come_from_floor(base, master_profile):
    cv, _, _ = _engine(base, master_profile, [STEP1, STEP2, STEP3])
    assert cv["identity"]["name"] == "Test Person"
    assert cv["education"][0]["institution"] == "University of Leeds"
    assert cv["certifications"] == ["Floor cert."]
    assert cv["languages"] == ["English (Native)"]


def test_report_carries_rubric_gaps_and_provenance(base, master_profile):
    _, report, _ = _engine(base, master_profile, [STEP1, STEP2, STEP3])
    assert report["rubric"] == STEP1["rubric"]
    assert report["gaps"] == STEP2["gaps"]
    assert report["provenance"]["experience.siffa"] == "master_profile"
    assert report["provenance"]["leadership.product_design_society"] == "master_profile"


def test_lean_template_skips_disabled_sections(base, master_profile):
    # lean disables projects and leadership; only experience is selectable.
    step2 = {"selection": {"experience": [{"identity": "siffa", "rationale": "fit"}]}, "gaps": []}
    step3 = {"objective": "Lean objective.", "bullets": {"siffa": ["Lean bullet."]},
             "skills_columns": [], "skill_tags": ["Figma"]}
    cv, report, _ = _engine(base, master_profile, [STEP1, step2, step3], template_id="lean")
    assert cv["experience"][0]["bullets"] == ["Lean bullet."]
    # projects/leadership keep floor content (render hides them via the manifest).
    assert "projects" not in report["selection"] or report["selection"].get("projects") == []


def test_validation_passes_for_assembled_output(base, master_profile):
    from pipeline.cv_schema import validate_cv_content

    cv, _, _ = _engine(base, master_profile, [STEP1, STEP2, STEP3])
    assert validate_cv_content(cv) == []


def test_collect_reservoir_pulls_pools(master_profile):
    pools = cv_engine.collect_reservoir(master_profile)
    assert pools["soft_skills"] == ["Adaptable across environments."]
    assert pools["technical_skills"]["cad"] == ["SolidWorks"]


def test_mapping_threads_into_prompts(base, master_profile):
    mapping = {
        "narrative_hint": "LEAD WITH DESIGN CRAFT",
        "experience_priority": ["siffa"],
        "deprioritise": ["ashtar"],
        "project_emphasis": ["pill_pod"],
        "skills_emphasis": ["ui_ux"],
        "default_template": "full",
    }
    caller = SequenceCaller([json.dumps(STEP1), json.dumps(STEP2), json.dumps(STEP3)])
    cv_engine.run_engine(
        {"title": "x", "employer": "", "description": ""},
        base=base, master_profile=master_profile, template_id="full", caller=caller, mapping=mapping,
    )
    step1_prompt, step2_prompt, step3_prompt = caller.prompts
    assert "LEAD WITH DESIGN CRAFT" in step1_prompt
    assert "LEAD WITH DESIGN CRAFT" in step3_prompt
    assert "experience_priority" in step2_prompt and "siffa" in step2_prompt
    assert "deprioritise" in step2_prompt and "ashtar" in step2_prompt


def test_no_mapping_leaves_no_unfilled_placeholders(base, master_profile):
    _, _, caller = _engine(base, master_profile, [STEP1, STEP2, STEP3])
    joined = "".join(caller.prompts)
    assert "{{NARRATIVE_HINT}}" not in joined
    assert "{{PRIORS}}" not in joined
