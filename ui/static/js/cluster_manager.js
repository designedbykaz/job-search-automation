/**
 * Cluster manager on the Run page: list, create, edit, toggle, delete via /clusters API.
 */

(function () {
  "use strict";

  const DELETE_CONFIRM_MS = 3000;

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s == null ? "" : String(s);
    return div.innerHTML;
  }

  function getModal() {
    const el = document.getElementById("clusterModal");
    return el ? bootstrap.Modal.getOrCreateInstance(el) : null;
  }

  function keywordCount(cluster) {
    const kw = cluster.keywords;
    return Array.isArray(kw) ? kw.length : 0;
  }

  async function loadClusters() {
    const tbody = document.getElementById("clusterTableBody");
    if (!tbody) return;

    try {
      const res = await fetch("/clusters/list");
      if (!res.ok) {
        tbody.innerHTML =
          '<tr><td colspan="4" class="text-center text-muted">Failed to load clusters.</td></tr>';
        return;
      }
      const clusterList = await res.json();
      renderClusterTable(clusterList);
    } catch (_err) {
      tbody.innerHTML =
        '<tr><td colspan="4" class="text-center text-muted">Failed to load clusters.</td></tr>';
    }
  }

  function renderClusterTable(clusterList) {
    const tbody = document.getElementById("clusterTableBody");
    if (!tbody) return;

    if (!clusterList || clusterList.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="4" class="text-center text-muted">No clusters yet. Click "New cluster" to create one.</td></tr>';
      return;
    }

    tbody.innerHTML = clusterList
      .map(function (c) {
        const id = escapeHtml(c.id);
        const label = escapeHtml(c.label);
        const active = c.active ? "checked" : "";
        const count = keywordCount(c);
        return (
          '<tr data-cluster-id="' +
          id +
          '">' +
          '<td><div class="form-check form-switch">' +
          '<input class="form-check-input cluster-toggle" type="checkbox" ' +
          active +
          ' data-cluster-id="' +
          id +
          '">' +
          "</div></td>" +
          "<td>" +
          label +
          "</td>" +
          '<td><span class="badge bg-secondary">' +
          count +
          "</span></td>" +
          "<td>" +
          '<button type="button" class="btn btn-sm btn-outline-secondary edit-cluster-btn" data-cluster-id="' +
          id +
          '" title="Edit"><i class="bi bi-pencil"></i></button> ' +
          '<button type="button" class="btn btn-sm btn-outline-danger delete-cluster-btn" data-cluster-id="' +
          id +
          '" title="Delete" data-confirming="0"><i class="bi bi-trash"></i></button>' +
          "</td>" +
          "</tr>"
        );
      })
      .join("");

    attachRowHandlers();
  }

  function attachRowHandlers() {
    document.querySelectorAll(".cluster-toggle").forEach(function (el) {
      el.addEventListener("change", toggleCluster);
    });
    document.querySelectorAll(".edit-cluster-btn").forEach(function (el) {
      el.addEventListener("click", openModalForEdit);
    });
    document.querySelectorAll(".delete-cluster-btn").forEach(function (el) {
      el.addEventListener("click", deleteCluster);
    });
  }

  async function toggleCluster(event) {
    const clusterId = event.target.dataset.clusterId;
    const res = await fetch("/clusters/" + encodeURIComponent(clusterId) + "/toggle", {
      method: "POST",
    });
    if (!res.ok) {
      alert("Failed to toggle cluster");
      loadClusters();
    }
  }

  function openModalForCreate() {
    document.getElementById("clusterModalTitle").textContent = "New cluster";
    document.getElementById("clusterIdInput").value = "";
    document.getElementById("clusterLabelInput").value = "";
    document.getElementById("clusterKeywordsInput").value = "";
    document.getElementById("clusterActiveInput").checked = true;
    document.getElementById("clusterModalError").classList.add("d-none");
    const modal = getModal();
    if (modal) modal.show();
  }

  async function openModalForEdit(event) {
    const btn = event.target.closest(".edit-cluster-btn");
    if (!btn) return;
    const clusterId = btn.dataset.clusterId;

    const res = await fetch("/clusters/list");
    if (!res.ok) {
      alert("Failed to load cluster");
      return;
    }
    const all = await res.json();
    const cluster = all.find(function (c) {
      return c.id === clusterId;
    });
    if (!cluster) {
      alert("Cluster not found");
      return;
    }

    const keywords = Array.isArray(cluster.keywords) ? cluster.keywords : [];
    document.getElementById("clusterModalTitle").textContent = "Edit: " + cluster.label;
    document.getElementById("clusterIdInput").value = cluster.id;
    document.getElementById("clusterLabelInput").value = cluster.label;
    document.getElementById("clusterKeywordsInput").value = keywords.join("\n");
    document.getElementById("clusterActiveInput").checked = !!cluster.active;
    document.getElementById("clusterModalError").classList.add("d-none");
    const modal = getModal();
    if (modal) modal.show();
  }

  async function saveCluster() {
    const id = document.getElementById("clusterIdInput").value;
    const label = document.getElementById("clusterLabelInput").value.trim();
    const keywordsText = document.getElementById("clusterKeywordsInput").value;
    const keywords = keywordsText
      .split("\n")
      .map(function (s) {
        return s.trim();
      })
      .filter(function (s) {
        return s.length > 0;
      });
    const active = document.getElementById("clusterActiveInput").checked;
    const errorEl = document.getElementById("clusterModalError");
    const saveBtn = document.getElementById("clusterSaveBtn");

    if (!label) {
      errorEl.textContent = "Cluster name is required";
      errorEl.classList.remove("d-none");
      return;
    }

    const url = id
      ? "/clusters/" + encodeURIComponent(id) + "/update"
      : "/clusters/create";

    if (saveBtn) saveBtn.disabled = true;
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ label: label, keywords: keywords, active: active }),
      });

      if (!res.ok) {
        let msg = "Failed to save cluster";
        try {
          const errorData = await res.json();
          if (errorData && errorData.error) msg = errorData.error;
        } catch (_e) {
          /* ignore */
        }
        errorEl.textContent = msg;
        errorEl.classList.remove("d-none");
        return;
      }

      const modal = getModal();
      if (modal) modal.hide();
      loadClusters();
    } finally {
      if (saveBtn) saveBtn.disabled = false;
    }
  }

  function resetDeleteConfirm(btn) {
    btn.dataset.confirming = "0";
    btn.classList.remove("is-confirming", "btn-danger");
    btn.classList.add("btn-outline-danger");
    btn.title = "Delete";
  }

  function armDeleteConfirm(btn) {
    btn.dataset.confirming = "1";
    btn.classList.add("is-confirming", "btn-danger");
    btn.classList.remove("btn-outline-danger");
    btn.title = "Click again to confirm delete";
    setTimeout(function () {
      if (btn.dataset.confirming === "1") {
        resetDeleteConfirm(btn);
      }
    }, DELETE_CONFIRM_MS);
  }

  async function runClusterScrape() {
    const btn = document.getElementById("runClusterScrapeBtn");
    const locationInput = document.getElementById("clusterScrapeLocation");
    const summaryEl = document.getElementById("clusterScrapeSummary");
    const location = locationInput ? locationInput.value.trim() : "";
    const defaultBtnHtml = '<i class="bi bi-play-fill"></i> Run cluster scrape';

    if (!btn || !summaryEl) return;

    btn.disabled = true;
    btn.innerHTML =
      '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Scraping...';
    summaryEl.innerHTML =
      '<div class="alert alert-info mb-0">Scrape running. This can take several minutes depending on how many keywords are active. Do not close this tab.</div>';

    try {
      const res = await fetch("/clusters/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cluster_ids: null,
          location: location || null,
        }),
      });

      let data = {};
      try {
        data = await res.json();
      } catch (_parseErr) {
        data = {};
      }

      if (!res.ok) {
        summaryEl.innerHTML =
          '<div class="alert alert-danger mb-0"><strong>Scrape failed.</strong><br>' +
          escapeHtml(data.error || "Unknown error") +
          "</div>";
        return;
      }

      summaryEl.innerHTML =
        '<div class="alert alert-success mb-0">' +
        "<strong>Scrape complete.</strong>" +
        '<ul class="mb-2 mt-2">' +
        "<li>Scraped: " +
        escapeHtml(String(data.scraped != null ? data.scraped : 0)) +
        " raw results</li>" +
        "<li>After dedup: " +
        escapeHtml(String(data.deduplicated != null ? data.deduplicated : 0)) +
        " unique jobs</li>" +
        "<li>Matched cluster keywords: " +
        escapeHtml(String(data.matched != null ? data.matched : 0)) +
        " jobs</li>" +
        "<li>Logged to Sheet: " +
        escapeHtml(String(data.logged_to_sheet != null ? data.logged_to_sheet : 0)) +
        " (errors: " +
        escapeHtml(String(data.sheet_errors != null ? data.sheet_errors : 0)) +
        ")</li>" +
        "<li>Total indexed: " +
        escapeHtml(String(data.indexed != null ? data.indexed : 0)) +
        " jobs</li>" +
        "</ul>" +
        '<a href="/jobs/" class="btn btn-sm btn-dark">View jobs</a>' +
        "</div>";
    } catch (err) {
      summaryEl.innerHTML =
        '<div class="alert alert-danger mb-0"><strong>Network error.</strong><br>' +
        escapeHtml(err && err.message ? err.message : String(err)) +
        "</div>";
    } finally {
      btn.disabled = false;
      btn.innerHTML = defaultBtnHtml;
    }
  }

  async function deleteCluster(event) {
    const btn = event.target.closest(".delete-cluster-btn");
    if (!btn) return;
    const clusterId = btn.dataset.clusterId;

    if (btn.dataset.confirming !== "1") {
      armDeleteConfirm(btn);
      return;
    }

    resetDeleteConfirm(btn);

    const res = await fetch("/clusters/" + encodeURIComponent(clusterId) + "/delete", {
      method: "POST",
    });
    if (!res.ok) {
      alert("Failed to delete cluster");
      return;
    }
    loadClusters();
  }

  document.addEventListener("DOMContentLoaded", function () {
    const newBtn = document.getElementById("newClusterBtn");
    const saveBtn = document.getElementById("clusterSaveBtn");
    const runBtn = document.getElementById("runClusterScrapeBtn");
    if (newBtn) newBtn.addEventListener("click", openModalForCreate);
    if (saveBtn) saveBtn.addEventListener("click", saveCluster);
    if (runBtn) runBtn.addEventListener("click", runClusterScrape);
    loadClusters();
  });
})();
