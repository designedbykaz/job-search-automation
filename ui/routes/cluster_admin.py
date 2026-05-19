"""JSON API for cluster CRUD and cluster-based scrape."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from ui.services import cluster_search, clusters

bp = Blueprint("cluster_admin", __name__, url_prefix="/clusters")


@bp.get("/list")
def list_clusters_route():
    """Return all clusters as a JSON list, sorted by ID."""
    return jsonify(clusters.list_clusters())


@bp.post("/create")
def create_cluster_route():
    """Create a new cluster from JSON body. Returns the created cluster."""
    data = request.get_json(silent=True) or {}
    label = data.get("label", "").strip()
    keywords = data.get("keywords", [])
    active = bool(data.get("active", True))
    if not label:
        return jsonify({"error": "label is required"}), 400
    if not isinstance(keywords, list):
        return jsonify({"error": "keywords must be a list"}), 400
    try:
        cluster = clusters.create_cluster(label=label, keywords=keywords, active=active)
        return jsonify(cluster), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/<cluster_id>/update")
def update_cluster_route(cluster_id):
    """Update one or more fields of a cluster. Returns the updated cluster."""
    data = request.get_json(silent=True) or {}
    label = data.get("label")
    keywords = data.get("keywords")
    active = data.get("active")
    if label is not None and not isinstance(label, str):
        return jsonify({"error": "label must be a string"}), 400
    if keywords is not None and not isinstance(keywords, list):
        return jsonify({"error": "keywords must be a list"}), 400
    if active is not None and not isinstance(active, bool):
        return jsonify({"error": "active must be a boolean"}), 400
    try:
        updated = clusters.update_cluster(
            cluster_id,
            label=label.strip() if label is not None else None,
            keywords=keywords,
            active=active,
        )
        if not updated:
            return jsonify({"error": "Cluster not found"}), 404
        return jsonify(clusters.get_cluster(cluster_id))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/<cluster_id>/delete")
def delete_cluster_route(cluster_id):
    """Delete a cluster. Returns success status."""
    deleted = clusters.delete_cluster(cluster_id)
    if not deleted:
        return jsonify({"error": "Cluster not found"}), 404
    return jsonify({"deleted": True, "id": cluster_id})


@bp.post("/<cluster_id>/toggle")
def toggle_cluster_route(cluster_id):
    """Toggle the active state of a cluster."""
    cluster = clusters.get_cluster(cluster_id)
    if cluster is None:
        return jsonify({"error": "Cluster not found"}), 404
    new_active = not cluster.get("active", False)
    clusters.update_cluster(cluster_id, active=new_active)
    return jsonify({"id": cluster_id, "active": new_active})


@bp.post("/run")
def run_cluster_scrape_route():
    """Trigger a cluster-based scrape. Returns summary dict."""
    data = request.get_json(silent=True) or {}
    cluster_ids = data.get("cluster_ids")
    location = data.get("location")
    if cluster_ids is not None and not isinstance(cluster_ids, list):
        return jsonify({"error": "cluster_ids must be a list or null"}), 400
    try:
        result = cluster_search.run_cluster_search(
            cluster_ids=cluster_ids,
            location=location,
        )
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
