# scripts/migrate_clusters.py
"""One-shot migration: populate config/clusters.json from config/keywords.py.

Usage:
    python -m scripts.migrate_clusters
    python -m scripts.migrate_clusters --force
"""

from __future__ import annotations

import argparse
import sys

from config.keywords import ACTIVE_CLUSTERS, KEYWORDS_BY_CLUSTER
from ui.services import clusters


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate config/clusters.json from config/keywords.py"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing clusters in config/clusters.json",
    )
    args = parser.parse_args()

    data = clusters._read_file()
    existing = data.get("clusters", {})
    if isinstance(existing, dict) and existing and not args.force:
        print(
            "config/clusters.json already has clusters. "
            "Use --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.force and isinstance(existing, dict) and existing:
        clusters._write_clusters({"version": 1, "clusters": {}})

    created_rows: list[dict] = []
    try:
        for cluster_name, keywords in KEYWORDS_BY_CLUSTER.items():
            active = ACTIVE_CLUSTERS.get(cluster_name, False)
            row = clusters.create_cluster(cluster_name, keywords, active=active)
            created_rows.append(row)
    except Exception as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Created {len(created_rows)} cluster(s):")
    for row in created_rows:
        print(f"  {row['id']}: {row['label']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
