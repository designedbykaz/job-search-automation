# tailor.py � tailors CV JSON and cover letter per job via Claude API

import anthropic
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def load_json(filepath):
    """Open and return parsed JSON from filepath (UTF-8)."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt(filename):
    """Return text content of prompts/{filename} (UTF-8)."""
    prompt_path = Path("prompts") / filename
    with open(
        prompt_path, "r", encoding="utf-8-sig", errors="replace"
    ) as f:
        return f.read()


def save_json(data, filepath):
    """Save dict as formatted JSON (indent=2); create parent dirs; UTF-8."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _read_template_choice(output_folder):
    """Read the explicit per-job CV template choice (``a``/``b``/``c``), or
    ``None`` if the job has no choice file. Mirrors the file convention of
    ``ui.services.cv_template_choice`` (kept inline so the pipeline layer has no
    UI dependency), but returns ``None`` rather than defaulting, so the caller
    can fall back to the cluster's default template. Keep the two in step.
    """
    path = Path(output_folder) / "cv_template_choice.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    choice = str(data.get("template", "")).lower()
    return choice if choice in ("a", "b", "c") else None


def _read_cluster_for_folder(output_folder, index_path=None):
    """Resolve a job's cluster id (``CLU_N``) from the disk index, or ``None``.

    The index (``outputs/_index.json``) is the source of truth and stores each
    job's stable cluster id and its repo-relative output folder. We match the
    entry whose output folder resolves to the same absolute path as
    ``output_folder``. Fail-soft: any missing file, parse error, or no match
    yields ``None`` so tailoring is never blocked. Never touches the network.
    """
    repo_root = Path(__file__).resolve().parents[1]
    path = Path(index_path) if index_path is not None else repo_root / "outputs" / "_index.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    jobs = data.get("jobs") if isinstance(data, dict) else None
    entries = jobs.values() if isinstance(jobs, dict) else jobs if isinstance(jobs, list) else []
    try:
        target = Path(output_folder).resolve()
    except (OSError, ValueError):
        return None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        folder = entry.get("output_folder")
        if not folder:
            continue
        candidate = Path(folder)
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        try:
            if candidate.resolve() == target:
                return entry.get("cluster") or None
        except (OSError, ValueError):
            continue
    return None


def tailor_cv(job, output_folder):
    """
    Produce tailored CV JSON via the three-call engine; save under output_folder.

    The chosen template (read from the job's output folder, defaulting to plain)
    gives the engine its slot caps. Output is the structured schema, merged over
    the base CV floor. A secondary tailoring report (rubric, selection, gaps,
    provenance) is written fail-soft alongside it. Signature and call site are
    unchanged; only the internals are the new engine.
    """
    try:
        base_cv = load_json("content/base_cv_content.json")
        master_profile = load_json("content/master_profile.json")

        from pipeline.cv_engine import run_engine, EngineParseError
        from pipeline.cv_render import resolve_template_id
        from pipeline import cluster_map

        cluster_id = _read_cluster_for_folder(output_folder)
        mapping = cluster_map.get_mapping(cluster_id)

        # Template precedence: explicit per-job choice, else the cluster's
        # default template, else (via get_mapping defaults) plain.
        explicit_choice = _read_template_choice(output_folder)
        template_id = resolve_template_id(
            explicit_choice if explicit_choice is not None else mapping["default_template"]
        )

        try:
            tailored, report = run_engine(
                job,
                base=base_cv,
                master_profile=master_profile,
                template_id=template_id,
                mapping=mapping,
            )
        except EngineParseError as exc:
            output_folder.mkdir(parents=True, exist_ok=True)
            raw_path = output_folder / "cv_tailored_raw.txt"
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(exc.raw)
            raise ValueError(
                f"Engine step {exc.step!r} returned unparseable JSON after stripping "
                f"code fences. Raw response saved to {raw_path}."
            ) from None

        out_path = output_folder / "cv_tailored.json"
        save_json(tailored, out_path)

        # Secondary, fail-soft: a report never blocks the primary CV write.
        try:
            save_json(report, output_folder / "cv_tailoring_report.json")
        except Exception as report_exc:
            print(f"Warning: failed to write tailoring report: {report_exc!r}")

        print(f"CV tailored for: {job['title']} at {job.get('employer', '')}")
        return tailored
    except Exception as e:
        print(
            f"Error in tailor_cv for job '{job.get('title', 'unknown')}': {e!r}"
        )
        raise


def tailor_cover_letter(job, output_folder):
    """
    Produce tailored cover letter as JSON (four paragraph keys); save under output_folder.
    """
    try:
        base_cv = load_json("content/base_cv_content.json")
        master_profile = load_json("content/master_profile.json")
        prompt = load_prompt("cover_letter_prompt.txt")

        filled_prompt = prompt.replace("{{BASE_CV}}", json.dumps(base_cv, indent=2))
        filled_prompt = filled_prompt.replace(
            "{{MASTER_PROFILE}}",
            json.dumps(master_profile["cover_letter"], indent=2),
        )
        filled_prompt = filled_prompt.replace("{{JOB_TITLE}}", job["title"])
        filled_prompt = filled_prompt.replace("{{EMPLOYER}}", job.get("employer", ""))
        filled_prompt = filled_prompt.replace(
            "{{JOB_DESCRIPTION}}", job.get("description", "")
        )

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-opus-4-6"),
            max_tokens=2048,
            messages=[{"role": "user", "content": filled_prompt}],
        )
        text = message.content[0].text
        cleaned = re.sub(r"```(?:json)?|```", "", text).strip()

        try:
            cover_letter_data = json.loads(cleaned)
        except json.JSONDecodeError:
            raw_path = output_folder / "cover_letter_tailored_raw.txt"
            output_folder.mkdir(parents=True, exist_ok=True)
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(text)
            raise ValueError(
                "Cover letter API response could not be parsed as JSON after stripping code fences. "
                f"Raw response saved to {raw_path}."
            ) from None

        out_path = output_folder / "cover_letter_tailored.json"
        save_json(cover_letter_data, out_path)

        print(
            f"Cover letter written for: {job['title']} at {job.get('employer', '')}"
        )
        return cover_letter_data
    except Exception as e:
        print(
            f"Error in tailor_cover_letter for job '{job.get('title', 'unknown')}': {e!r}"
        )
        raise
