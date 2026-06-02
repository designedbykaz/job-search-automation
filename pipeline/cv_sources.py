"""Layered CV content sources: the resolver and the content index.

Per identity, pick the richest available body across three tiers, in priority
order: the vault, then ``master_profile``, then the ``base_cv_content`` floor.
The resolver records which tier won and whether the chosen body is
``substantial`` (rich enough to use rather than a thin stub).

Two design rules hold this together:

- **The floor is the registry.** ``base_cv_content`` already holds every item,
  in its correct section, with verified factual fields (role, company, dates).
  Each floor item carries a stable ``id`` that names its identity. So which
  items exist, which section they sit in, and their facts all come from the
  floor. The vault and ``master_profile`` only supply richer body text.
- **Never invent.** Missing content yields empty bodies and the ``none`` tier,
  never fabricated text.

One quirk is encoded explicitly: ``master_profile`` lumps leadership under
``cv.experience``, so a leadership identity looks up its richer body in the
experience pool while keeping its facts from the floor's ``leadership`` item.

No engine here. Both functions are pure given their source dicts, which makes
them testable against fixtures with no API calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

# Joined non-empty body must reach this many characters to count as
# "substantial". Tunable. Mainly guards against a stub vault file later
# overriding richer master_profile content.
SUBSTANTIAL_MIN_CHARS = 120

TIER_VAULT = "vault"
TIER_MASTER_PROFILE = "master_profile"
TIER_BASE = "base"
TIER_NONE = "none"

# The identity-bearing schema sections the resolver and index cover. objective,
# certifications, languages, skill_tags and skills_columns are not single-item
# identities; they are filled mechanically or synthesised from reservoir pools
# in later phases, not resolved per identity here.
IDENTITY_SECTIONS = ("education", "projects", "leadership", "experience")

# Section in the CV schema -> the master_profile.cv pool its body lives in.
# Leadership identities draw their body from the experience pool.
_SECTION_TO_MP_POOL = {
    "education": "education",
    "projects": "projects",
    "leadership": "experience",
    "experience": "experience",
}

# Factual fields carried unchanged from the floor item, per section.
_FACT_FIELDS = {
    "education": ("institution", "subline", "dates", "qualification"),
    "projects": ("title", "stack"),
    "leadership": ("role", "org", "dates"),
    "experience": ("role", "company", "dates"),
}

# Where each section keeps its body lines in a floor item.
_FLOOR_BULLET_KEY = {
    "education": "details",
    "projects": "bullets",
    "leadership": "bullets",
    "experience": "bullets",
}

VAULT_DIRNAME = "profile"

_CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"


def _clean_lines(lines) -> list[str]:
    """Coerce a value into a list of non-empty, stripped strings."""
    out: list[str] = []
    if not isinstance(lines, (list, tuple)):
        return out
    for line in lines:
        if line is None:
            continue
        text = str(line).strip()
        if text:
            out.append(text)
    return out


def _is_substantial(lines) -> bool:
    cleaned = _clean_lines(lines)
    if not cleaned:
        return False
    return sum(len(line) for line in cleaned) >= SUBSTANTIAL_MIN_CHARS


def _floor_index(base: dict) -> dict[str, dict[str, dict]]:
    """Map ``section -> {id -> floor item}`` for identity-bearing sections.

    Items without an ``id`` are skipped: an item the floor cannot name cannot
    be joined to a master_profile pool or vault file.
    """
    index: dict[str, dict[str, dict]] = {s: {} for s in IDENTITY_SECTIONS}
    if not isinstance(base, dict):
        return index
    for section in IDENTITY_SECTIONS:
        for item in base.get(section) or []:
            if not isinstance(item, dict):
                continue
            identity = item.get("id")
            if identity:
                index[section][identity] = item
    return index


def _body_from_floor(item: Optional[dict], section: str) -> list[str]:
    if not item:
        return []
    return _clean_lines(item.get(_FLOOR_BULLET_KEY[section]))


def _body_from_master_profile(
    master_profile: dict, section: str, identity: str
) -> list[str]:
    cv = master_profile.get("cv") if isinstance(master_profile, dict) else None
    if not isinstance(cv, dict):
        return []
    pool = cv.get(_SECTION_TO_MP_POOL[section])
    if not isinstance(pool, dict):
        return []
    return _clean_lines(pool.get(identity))


def _split_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    """Split a leading ``---`` fenced frontmatter block from the body.

    Frontmatter is minimal ``key: value`` lines (no PyYAML, to keep the zero
    dependency rule). Returns ``(meta, body_lines)``. A file with no opening
    fence, or an unterminated one, is treated as all body with empty meta.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines
    meta: dict[str, str] = {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return meta, lines[i + 1:]
        key, sep, value = lines[i].partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    # No closing fence: malformed, so keep nothing as meta and treat as body.
    return {}, lines


def _vault_body_lines(body_lines) -> list[str]:
    """Best-effort markdown body: drop headings/fences, strip bullet markers."""
    out: list[str] = []
    for raw in body_lines:
        text = raw.strip()
        if not text or text.startswith("#") or text == "---":
            continue
        if text.startswith(("- ", "* ")):
            text = text[2:].strip()
        if text:
            out.append(text)
    return out


def index_vault(vault_dir) -> dict[str, list[Path]]:
    """Scan ``vault_dir`` recursively for markdown nodes, mapping ``id -> paths``.

    A node's id is its frontmatter ``id:`` if present, else its filename stem
    (so a flat ``profile/<id>.md`` still resolves without frontmatter). Several
    nodes may share one id; their bodies are concatenated downstream. Nodes whose
    id matches no floor item are simply never looked up: harmless research
    substrate. Unreadable files are skipped (fail-soft: a broken note must never
    block tailoring).
    """
    index: dict[str, list[Path]] = {}
    if not vault_dir:
        return index
    root = Path(vault_dir)
    if not root.is_dir():
        return index
    for path in sorted(root.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, _ = _split_frontmatter(text)
        identity = meta.get("id") or path.stem
        if identity:
            index.setdefault(identity, []).append(path)
    return index


def _body_from_vault(identity: str, vault_index: dict[str, list[Path]]) -> list[str]:
    """Concatenate the body lines of every vault node sharing ``identity``.

    Nodes are read in the sorted-path order ``index_vault`` recorded, so a
    multi-node identity assembles deterministically.
    """
    lines: list[str] = []
    for path in vault_index.get(identity, []):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        _, body = _split_frontmatter(text)
        lines.extend(_vault_body_lines(body))
    return lines


def _facts_from_floor(item: Optional[dict], section: str) -> dict[str, str]:
    fields = _FACT_FIELDS[section]
    if not item:
        return {field: "" for field in fields}
    return {field: str(item.get(field) or "") for field in fields}


def _record(
    identity: str,
    section: str,
    tier: str,
    body: list[str],
    floor_item: Optional[dict],
    *,
    substantial: bool,
) -> dict:
    return {
        "identity": identity,
        "section": section,
        "tier": tier,
        "substantial": substantial,
        "facts": _facts_from_floor(floor_item, section),
        # The richest source body, for synthesis input.
        "body": list(body),
        # The floor's verified bullets, the safe fallback for final output.
        "floor_body": _body_from_floor(floor_item, section),
    }


def resolve_item(
    identity: str,
    section: str,
    *,
    master_profile: dict,
    base: dict,
    vault_dir=None,
    vault_index=None,
) -> dict:
    """Resolve one identity to its richest available body and tier.

    Walks vault -> master_profile -> floor, taking the first tier whose body is
    substantial; if none clear the bar, takes the first tier with any content;
    if all are empty, returns the ``none`` tier with an empty body. Factual
    fields always come from the floor item, regardless of which tier wins.

    Pass a prebuilt ``vault_index`` (from ``index_vault``) to scan the vault
    once across many items; otherwise it is built from ``vault_dir`` per call.
    """
    if section not in IDENTITY_SECTIONS:
        raise ValueError(
            f"unknown identity section {section!r}; "
            f"expected one of {IDENTITY_SECTIONS}"
        )

    if vault_index is None:
        vault_index = index_vault(vault_dir)

    floor_item = _floor_index(base)[section].get(identity)

    candidates = (
        (TIER_VAULT, _body_from_vault(identity, vault_index)),
        (TIER_MASTER_PROFILE, _body_from_master_profile(master_profile, section, identity)),
        (TIER_BASE, _body_from_floor(floor_item, section)),
    )

    for tier, body in candidates:
        if _is_substantial(body):
            return _record(identity, section, tier, body, floor_item, substantial=True)

    for tier, body in candidates:
        if body:
            return _record(identity, section, tier, body, floor_item, substantial=False)

    return _record(identity, section, TIER_NONE, [], floor_item, substantial=False)


def _title_for(section: str, facts: dict[str, str]) -> str:
    if section == "projects":
        return facts.get("title", "")
    if section == "education":
        return facts.get("institution", "")
    role = facts.get("role", "")
    org = facts.get("company") or facts.get("org") or ""
    if role and org:
        return f"{role}, {org}"
    return role or org


def build_content_index(
    *, master_profile: dict, base: dict, vault_dir=None, vault_index=None
) -> list[dict]:
    """Build the lightweight index the engine's selection step ranks against.

    One record per floor item (the floor defines what exists), in floor order:
    ``identity, section, title, first_line, tier, substantial``. The title and
    facts come from the floor; the first line and tier come from the resolver.

    The vault is scanned once here (or reuses a prebuilt ``vault_index``) and
    threaded into every ``resolve_item`` call.
    """
    if vault_index is None:
        vault_index = index_vault(vault_dir)
    records: list[dict] = []
    floor_index = _floor_index(base)
    for section in IDENTITY_SECTIONS:
        for identity in floor_index[section]:
            resolved = resolve_item(
                identity,
                section,
                master_profile=master_profile,
                base=base,
                vault_index=vault_index,
            )
            body = resolved["body"]
            records.append(
                {
                    "identity": identity,
                    "section": section,
                    "title": _title_for(section, resolved["facts"]),
                    "first_line": body[0] if body else "",
                    "tier": resolved["tier"],
                    "substantial": resolved["substantial"],
                }
            )
    return records


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_default_sources() -> tuple[dict, dict]:
    """Load the real ``master_profile`` and ``base`` content from ``content/``.

    Convenience for callers and smoke tests. Returns ``(master_profile, base)``.
    Resolves paths from the package root so it is independent of the cwd.
    """
    master_profile = _load_json(_CONTENT_DIR / "master_profile.json")
    base = _load_json(_CONTENT_DIR / "base_cv_content.json")
    return master_profile, base
