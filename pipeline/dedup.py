# dedup.py � deduplicate, filter by keywords, and prepare per-job output folders

import json
import re, os
from datetime import date
from pathlib import Path

def deduplicate(all_jobs):
    """
    Remove duplicates where title.lower() + employer.lower() match exactly.
    Preserves the first occurrence of each duplicate.
    """
    seen = set()
    unique = []

    for job in all_jobs:
        key = (job.get("title", "").lower(), job.get("employer", "").lower())
        if key not in seen:
            seen.add(key)
            unique.append(job)

    return unique


def filter_by_keywords(jobs, keyword_to_cluster_map):
    """
    Return only jobs whose title contains at least one keyword from the map.
    Matched jobs are tagged with their cluster ID (e.g. 'CLU_1').
    Parameters:
        jobs: list of job dicts.
        keyword_to_cluster_map: dict mapping lowercased keyword to cluster ID.
            Typically produced by clusters.get_keyword_to_cluster_map().
    """
    matched = []

    for job in jobs:
        title = job.get("title", "").lower()
        for kw, cluster_id in keyword_to_cluster_map.items():
            if kw in title:
                job["cluster"] = cluster_id
                matched.append(job)
                break

    return matched


def make_folder_name(job):
    """
    Safe folder name: {source}_{title}_{employer}, lowercase, spaces -> underscores,
    only alphanumeric and underscores, max 80 characters.
    """
    source = str(job.get("source", "") or "")
    title = str(job.get("title", "") or "")
    employer = str(job.get("employer", "") or "")

    raw = f"{source}_{title}_{employer}".lower().replace(" ", "_")
    raw = re.sub(r"[^a-z0-9_]", "", raw)
    raw = re.sub(r"_+", "_", raw).strip("_")

    if not raw:
        raw = "job"

    if len(raw) > 80:
        raw = raw[:80]

    return raw


def create_output_folders(jobs):
    """
    For each job: outputs/{YYYY-MM-DD}/{folder}/job.json, set job['output_folder'].
    Returns the same list with output_folder added to each dict.
    """
    today_str = date.today().isoformat()
    base = Path("outputs") / today_str

    for job in jobs:
        folder_name = make_folder_name(job)
        out_dir = base / folder_name
        out_dir.mkdir(parents=True, exist_ok=True)

        job["output_folder"] = os.path.normpath(str(out_dir))

        job_json_path = out_dir / "job.json"
        with open(job_json_path, "w", encoding="utf-8") as f:
            json.dump(job, f, indent=2, ensure_ascii=False)

    return jobs
