"""The three-call CV tailoring engine.

Replaces the single v1 prompt with three orchestrated Claude calls operating on
the structured CV schema:

1. Analysis and rubric. Reads the job and the chosen template's slot caps,
   returns a JD profile and an abstract ranked rubric with no invented
   specifics.
2. Select, rank, gap report. Reads the rubric and the lightweight content index
   (from the Phase 1 data layer), assigns real item identities to the tailored
   slots, and reports rubric priorities with no supporting evidence.
3. Grounded synthesis. Reads the full body of only the selected items plus the
   reservoir pools, and writes the tailored prose.

Two grounding guarantees are enforced mechanically, not left to the prompt:

- **Facts travel from the floor.** The engine assembles each tailored item from
  the floor's factual fields (role, company, dates) plus only the bullets the
  model generated. The model never restates a role, company, or date.
- **The floor is the merge floor.** The structured output is merged over the
  base CV, so any field the model did not confidently produce keeps its
  verified value. The engine can only improve on the floor.

The Claude call is injected (``caller``) so every step is unit-testable with no
API access. ``tailor_cv`` wires this engine to disk; this module does no file
I/O on success, and on a step parse failure it raises ``EngineParseError``
carrying the raw text so the caller can preserve it.
"""

from __future__ import annotations

import json
import os
import re
from typing import Callable, Optional

from pipeline.cv_schema import normalize_cv_content, validate_cv_content
from pipeline.cv_sources import build_content_index, index_vault, resolve_item
from pipeline.manifest import load_manifest, section_enabled, section_max
from pipeline.tailor import load_prompt

# Tailored identity sections the model selects and writes. Education,
# certifications and languages are Tier 2 (mechanical) and never selected here.
TAILORED_IDENTITY_SECTIONS = ("experience", "projects", "leadership")

# Per-step token budgets. Synthesis writes the most.
_STEP1_MAX_TOKENS = 1500
_STEP2_MAX_TOKENS = 1500
_STEP3_MAX_TOKENS = 4096

Caller = Callable[..., str]


class EngineParseError(ValueError):
    """A step's response could not be parsed as JSON.

    Carries the failing ``step`` label and the ``raw`` response text so the
    caller can persist it, mirroring the v1 raw-save-on-failure behaviour.
    """

    def __init__(self, step: str, raw: str) -> None:
        super().__init__(f"step {step!r} did not return parseable JSON")
        self.step = step
        self.raw = raw


def _default_caller(prompt: str, *, max_tokens: int) -> str:
    """Real Claude call. Imported lazily so the engine imports without the SDK."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-opus-4-6"),
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _parse_json(text: str, step: str):
    """Strip code fences and parse JSON, or raise ``EngineParseError``."""
    import re

    cleaned = re.sub(r"```(?:json)?|```", "", text or "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise EngineParseError(step, text or "") from None


def _dump(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _slot_caps(manifest: dict) -> dict:
    """Enabled tailored sections mapped to their slot cap (``None`` = uncapped).

    Identity sections only. Used for the selection step and for capping the
    resolved items the orchestrator assembles.
    """
    caps: dict[str, Optional[int]] = {}
    for section in TAILORED_IDENTITY_SECTIONS:
        if section_enabled(manifest, section):
            caps[section] = section_max(manifest, section, default=None)
    return caps


# Non-identity output fields the synthesis step may also produce, gated by the
# manifest. The Step 3 prompt only generates these when the slot map names them.
_SYNTH_OUTPUT_FIELDS = ("skills_columns", "skill_tags")


def _output_slots(manifest: dict) -> dict:
    """Slot map for the synthesis step: identity caps plus the enabled
    non-identity output fields (skills_columns, skill_tags).

    Kept separate from ``_slot_caps`` so the selection path stays identity-only
    while Step 3 is told which skills fields it is allowed to fill.
    """
    slots = dict(_slot_caps(manifest))
    for field in _SYNTH_OUTPUT_FIELDS:
        if section_enabled(manifest, field):
            slots[field] = section_max(manifest, field, default=None)
    return slots


def _narrative_hint(mapping: Optional[dict]) -> str:
    return (mapping or {}).get("narrative_hint", "") or ""


def _priors(mapping: Optional[dict]) -> dict:
    """The cluster mapping's bias lists for the selection step's prompt.

    Item-level only. skills_emphasis is not here: it steers skill themes, not
    item selection, so it is threaded into the synthesis step instead.
    """
    m = mapping or {}
    return {
        "experience_priority": m.get("experience_priority", []),
        "deprioritise": m.get("deprioritise", []),
        "project_emphasis": m.get("project_emphasis", []),
    }


def _skills_emphasis(mapping: Optional[dict]) -> list:
    """The cluster mapping's preferred technical_skills theme labels, for
    synthesis. A nudge toward which themes to surface, not a lock."""
    return (mapping or {}).get("skills_emphasis", []) or []


def collect_reservoir(master_profile: dict) -> dict:
    """Pull the non-identity reservoir pools Step 3 draws on for objective,
    skills_columns and skill_tags. These fields are not single items, so the
    resolver does not cover them.
    """
    cv = master_profile.get("cv", {}) if isinstance(master_profile, dict) else {}
    return {
        "personal_profile": cv.get("personal_profile", []),
        "personal_motivations": cv.get("personal_motivations", []),
        "soft_skills": cv.get("soft_skills", []),
        "technical_skills": cv.get("technical_skills", {}),
        "certifications": cv.get("certifications", []),
        "languages": cv.get("languages", []),
    }


# --- the three steps -----------------------------------------------------


def run_step1(job: dict, manifest: dict, caller: Caller, mapping: Optional[dict] = None) -> dict:
    """Analysis and rubric. Returns ``{jd_profile, rubric}``."""
    prompt = (
        load_prompt("cv_step1_analysis.txt")
        .replace("{{JOB_TITLE}}", job.get("title", ""))
        .replace("{{EMPLOYER}}", job.get("employer", ""))
        .replace("{{JOB_DESCRIPTION}}", job.get("description", ""))
        .replace("{{SLOT_CAPS}}", _dump(_slot_caps(manifest)))
        .replace("{{NARRATIVE_HINT}}", _narrative_hint(mapping))
    )
    return _parse_json(caller(prompt, max_tokens=_STEP1_MAX_TOKENS), "analysis")


def run_step2(
    rubric: dict, index: list[dict], manifest: dict, caller: Caller, mapping: Optional[dict] = None
) -> dict:
    """Select, rank, gap report. Returns ``{selection, gaps}``.

    ``selection`` maps each enabled tailored section to a list of
    ``{identity, rationale}``; ``gaps`` lists unmet rubric priorities.
    """
    caps = _slot_caps(manifest)
    selectable = [r for r in index if r["section"] in caps]
    prompt = (
        load_prompt("cv_step2_select.txt")
        .replace("{{RUBRIC}}", _dump(rubric))
        .replace("{{SLOT_CAPS}}", _dump(caps))
        .replace("{{CONTENT_INDEX}}", _dump(selectable))
        .replace("{{PRIORS}}", _dump(_priors(mapping)))
    )
    return _parse_json(caller(prompt, max_tokens=_STEP2_MAX_TOKENS), "select")


def run_step3(
    rubric: dict,
    selection: dict,
    selected_content: dict,
    reservoir: dict,
    manifest: dict,
    caller: Caller,
    mapping: Optional[dict] = None,
) -> dict:
    """Grounded synthesis. Returns ``{objective, bullets, skills_columns,
    skill_tags}`` where ``bullets`` maps a selected identity to its generated
    bullet lines. Factual fields are assembled by the orchestrator, not here.
    """
    prompt = (
        load_prompt("cv_step3_synthesis.txt")
        .replace("{{RUBRIC}}", _dump(rubric))
        .replace("{{SELECTION}}", _dump(selection))
        .replace("{{SELECTED_CONTENT}}", _dump(selected_content))
        .replace("{{RESERVOIR}}", _dump(reservoir))
        .replace("{{SLOT_CAPS}}", _dump(_output_slots(manifest)))
        .replace("{{NARRATIVE_HINT}}", _narrative_hint(mapping))
        .replace("{{SKILLS_EMPHASIS}}", _dump(_skills_emphasis(mapping)))
    )
    return _parse_json(caller(prompt, max_tokens=_STEP3_MAX_TOKENS), "synthesis")


# --- orchestration -------------------------------------------------------


def _resolve_selected(
    selection: dict,
    *,
    master_profile: dict,
    base: dict,
    vault_index,
    caps: dict,
) -> tuple[dict, dict]:
    """Resolve each selected identity to its facts and body.

    Drops identities that are not in the floor (a hallucination guard) and caps
    each section to its slot count. Returns ``(resolved_map, ordered_selection)``
    where ``resolved_map`` is keyed by ``(section, identity)`` and
    ``ordered_selection`` is the cleaned, capped selection lists.
    """
    resolved_map: dict[tuple, dict] = {}
    ordered: dict[str, list] = {}
    for section, cap in caps.items():
        picks = selection.get(section) or []
        cleaned: list[dict] = []
        for pick in picks:
            identity = pick.get("identity") if isinstance(pick, dict) else None
            if not identity:
                continue
            resolved = resolve_item(
                identity, section, master_profile=master_profile, base=base, vault_index=vault_index
            )
            # Floor-grounding guard: skip anything the floor cannot name.
            if resolved["tier"] == "none":
                continue
            resolved_map[(section, identity)] = resolved
            cleaned.append({"identity": identity, "rationale": pick.get("rationale", "")})
            if cap is not None and len(cleaned) >= cap:
                break
        ordered[section] = cleaned
    return resolved_map, ordered


def _selected_content(ordered: dict, resolved_map: dict) -> dict:
    """Build the full-content payload Step 3 synthesises from."""
    payload: dict[str, list] = {}
    for section, picks in ordered.items():
        payload[section] = [
            {
                "identity": pick["identity"],
                "facts": resolved_map[(section, pick["identity"])]["facts"],
                "body": resolved_map[(section, pick["identity"])]["body"],
            }
            for pick in picks
        ]
    return payload


# Dated work-history sections are reordered into reverse-chronological order
# after selection; relevance decides what is included, the timeline decides the
# order shown. Projects carry no comparable dates, so they keep selection order.
_CHRONO_SECTIONS = ("experience", "leadership")
_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_ONGOING = ("present", "current", "ongoing", "now")


def _year_month(token: str, fallback_year: Optional[int] = None) -> tuple[int, int]:
    """Best-effort (year, month) from a date token like 'Oct 2025', '2018', or
    'Present'. Ongoing markers sort newest; a missing year borrows the fallback."""
    low = token.lower()
    if any(word in low for word in _ONGOING):
        return (9999, 13)
    year_match = re.search(r"(?:19|20)\d{2}", token)
    year = int(year_match.group()) if year_match else (fallback_year or 0)
    month_match = re.search(r"[A-Za-z]{3,}", token)
    month = _MONTHS.get(month_match.group()[:3].lower(), 0) if month_match else 0
    return (year, month)


def _chrono_key(dates: str) -> tuple:
    """Reverse-chronological sort key for a CV date range: the range end first
    (so current roles lead), then the start. Unparseable dates sort oldest, so a
    bad value sinks rather than jumping the list. A shared year on one side of
    'Mon - Mon YYYY' is borrowed by the side that lacks it."""
    text = str(dates or "").strip()
    if not text:
        return ((0, 0), (0, 0))
    parts = [p for p in re.split(r"\s*-\s*", text) if p.strip()] or [text]
    end = _year_month(parts[-1])
    start = _year_month(parts[0], fallback_year=end[0] or None)
    if end[0] == 0:
        end = _year_month(parts[-1], fallback_year=start[0] or None)
    return (end, start)


def _assemble_section(section: str, picks: list, resolved_map: dict, bullets: dict) -> list:
    """Combine floor facts with generated bullets into final items.

    Facts always come from the floor. Bullets prefer the model's output and fall
    back to the floor's verified bullets (not the raw reservoir body) so a
    section is never empty and never unpolished. Dated sections are returned in
    reverse-chronological order regardless of the selection (relevance) order.
    """
    items = []
    for pick in picks:
        identity = pick["identity"]
        resolved = resolved_map[(section, identity)]
        generated = bullets.get(identity) if isinstance(bullets, dict) else None
        cleaned = [str(b) for b in generated if b] if generated else []
        item = {"id": identity}
        item.update(resolved["facts"])
        item["bullets"] = cleaned or list(resolved["floor_body"])
        items.append(item)
    if section in _CHRONO_SECTIONS:
        items.sort(key=lambda it: _chrono_key(it.get("dates", "")), reverse=True)
    return items


def _merge_over_floor(base: dict, tailored: dict) -> dict:
    """Overlay produced tailored fields on the normalised floor.

    Anything the engine did not confidently produce keeps its floor value.
    Identity, education, certifications and languages always come from the floor.
    """
    merged = normalize_cv_content(base)
    if tailored.get("objective"):
        merged["objective"] = tailored["objective"]
    for section in TAILORED_IDENTITY_SECTIONS:
        if tailored.get(section):
            merged[section] = tailored[section]
    if tailored.get("skills_columns"):
        merged["skills_columns"] = tailored["skills_columns"]
    if tailored.get("skill_tags"):
        merged["skill_tags"] = tailored["skill_tags"]
    return merged


def run_engine(
    job: dict,
    *,
    base: dict,
    master_profile: dict,
    template_id: str,
    caller: Caller = _default_caller,
    vault_dir=None,
    mapping: Optional[dict] = None,
) -> tuple[dict, dict]:
    """Run the three-step engine and return ``(cv, report)``.

    ``cv`` is the structured, schema-valid tailored CV merged over the floor.
    ``report`` carries the rubric, the cleaned selection, the gap report and a
    per-item source-tier provenance map, for review. ``mapping`` is the optional
    cluster prior layer (narrative hint and favour/deprioritise lists); when
    absent the engine runs unbiased. Raises ``EngineParseError`` if any step
    returns unparseable JSON.
    """
    manifest = load_manifest(template_id)
    caps = _slot_caps(manifest)
    vault_index = index_vault(vault_dir)
    index = build_content_index(
        master_profile=master_profile, base=base, vault_index=vault_index
    )
    reservoir = collect_reservoir(master_profile)

    step1 = run_step1(job, manifest, caller, mapping)
    step2 = run_step2(step1, index, manifest, caller, mapping)

    resolved_map, ordered = _resolve_selected(
        step2.get("selection") or {},
        master_profile=master_profile,
        base=base,
        vault_index=vault_index,
        caps=caps,
    )
    selected_content = _selected_content(ordered, resolved_map)

    step3 = run_step3(step1, ordered, selected_content, reservoir, manifest, caller, mapping)

    bullets = step3.get("bullets") or {}
    tailored = {
        "objective": step3.get("objective", ""),
        "skills_columns": step3.get("skills_columns") or [],
        "skill_tags": step3.get("skill_tags") or [],
    }
    for section in TAILORED_IDENTITY_SECTIONS:
        if section in caps and ordered.get(section):
            tailored[section] = _assemble_section(section, ordered[section], resolved_map, bullets)

    merged = _merge_over_floor(base, tailored)

    problems = validate_cv_content(merged)
    if problems:
        raise ValueError("tailored CV failed schema validation: " + "; ".join(problems))

    provenance = {
        f"{section}.{identity}": resolved["tier"]
        for (section, identity), resolved in resolved_map.items()
    }
    report = {
        "jd_profile": step1.get("jd_profile", {}),
        "rubric": step1.get("rubric", []),
        "selection": ordered,
        "gaps": step2.get("gaps", []),
        "provenance": provenance,
    }
    return merged, report
