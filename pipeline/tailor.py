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


def tailor_cv(job, output_folder):
    """
    Produce tailored CV JSON from base + master profile + job; save under output_folder.
    """
    try:
        base_cv = load_json("content/base_cv_content.json")
        master_profile = load_json("content/master_profile.json")
        prompt = load_prompt("cv_prompt.txt")

        filled_prompt = prompt.replace("{{BASE_CV}}", json.dumps(base_cv, indent=2))
        filled_prompt = filled_prompt.replace(
            "{{MASTER_PROFILE}}", json.dumps(master_profile["cv"], indent=2)
        )
        filled_prompt = filled_prompt.replace("{{JOB_TITLE}}", job["title"])
        filled_prompt = filled_prompt.replace("{{EMPLOYER}}", job.get("employer", ""))
        filled_prompt = filled_prompt.replace(
            "{{JOB_DESCRIPTION}}", job.get("description", "")
        )

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-opus-4-6"),
            max_tokens=4096,
            messages=[{"role": "user", "content": filled_prompt}],
        )
        text = message.content[0].text
        cleaned = re.sub(r"```(?:json)?|```", "", text).strip()

        try:
            tailored = json.loads(cleaned)
        except json.JSONDecodeError:
            raw_path = output_folder / "cv_tailored_raw.txt"
            output_folder.mkdir(parents=True, exist_ok=True)
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(text)
            raise ValueError(
                "API response could not be parsed as JSON after stripping code fences. "
                f"Raw response saved to {raw_path}."
            ) from None

        out_path = output_folder / "cv_tailored.json"
        save_json(tailored, out_path)

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
