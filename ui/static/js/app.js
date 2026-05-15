(function () {
  "use strict";

  const CONFIRM_WINDOW_MS = 5000;
  const FADE_DELAY_MS = 2500;
  const PREVIEW_DEBOUNCE_MS = 400;

  const previewTimers = new Map();

  function escapeHtml(s) {
    if (s == null) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function buildDescriptionSection(job) {
    const parts = Array.isArray(job.description) ? job.description : [];
    let inner;
    if (parts.length) {
      inner = parts
        .map(function (para) {
          return '<p class="mb-2">' + escapeHtml(para) + "</p>";
        })
        .join("");
    } else {
      inner =
        '<p class="mb-0 text-secondary">No job description stored in the Sheet.</p>';
    }
    return (
      '<section class="mb-4">' +
      '<h3 class="section-title">Job description</h3>' +
      '<div class="border rounded p-3 small text-muted" style="max-height: 12rem; overflow-y: auto;">' +
      inner +
      "</div></section>"
    );
  }

  function buildActionRowSection(job, apiBase) {
    const r = job.row;
    const id = "job-action-row-" + r;
    const prefix = apiBase || "/jobs";
    let buttons = "";
    if (job.status === "to_review") {
      buttons =
        '<button type="button" class="btn btn-dark btn-job-approve flex-grow-1 d-inline-flex align-items-center justify-content-center gap-2" ' +
        'hx-post="' +
        prefix +
        "/" +
        r +
        '/approve" hx-target="#' +
        id +
        '" hx-swap="outerHTML">' +
        '<span class="btn-job-approve__spinner spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>' +
        '<span class="btn-job-approve__label d-inline-flex align-items-center gap-2"><i class="bi bi-check-lg"></i> Approve</span></button>' +
        '<button type="button" class="btn btn-outline-secondary flex-grow-1 d-inline-flex align-items-center justify-content-center gap-2" disabled>' +
        '<i class="bi bi-file-earmark-arrow-down"></i> Render PDF</button>' +
        '<button type="button" class="btn btn-outline-secondary d-inline-flex align-items-center gap-2" disabled title="Not available yet">' +
        '<i class="bi bi-archive"></i> Archive</button>';
    } else if (job.status === "approved") {
      buttons =
        '<button type="button" class="btn btn-outline-secondary d-inline-flex align-items-center gap-2" disabled title="Already approved">' +
        '<i class="bi bi-check-lg"></i> Approved</button>' +
        '<button type="button" class="btn btn-dark flex-grow-1 d-inline-flex align-items-center justify-content-center gap-2" disabled>' +
        '<i class="bi bi-file-earmark-arrow-down"></i> Render PDF</button>' +
        '<button type="button" class="btn btn-outline-secondary d-inline-flex align-items-center gap-2" disabled title="Not available yet">' +
        '<i class="bi bi-archive"></i> Archive</button>';
    } else if (job.status === "pdf_ready") {
      buttons =
        '<button type="button" class="btn btn-dark flex-grow-1 d-inline-flex align-items-center justify-content-center gap-2" disabled>' +
        '<i class="bi bi-file-earmark-arrow-down"></i> Download PDF</button>' +
        '<button type="button" class="btn btn-outline-secondary d-inline-flex align-items-center gap-2" disabled>' +
        '<i class="bi bi-arrow-clockwise"></i> Re-render</button>';
    }
    return (
      '<div id="' +
      id +
      '" class="p-4 border-top">' +
      '<div class="d-flex flex-wrap gap-2 align-items-center">' +
      buttons +
      "</div></div>"
    );
  }

  function jobsApiBase(layout) {
    const u = layout && layout.dataset && layout.dataset.jobsIndexUrl;
    if (!u) return "/jobs";
    return u.replace(/\/+$/, "") || "/jobs";
  }

  function openJobDetail(job, layout) {
    const r = job.row;
    const outFolder = job.output_folder != null ? String(job.output_folder) : "";
    const base = jobsApiBase(layout);
    const jobsIndexUrl = (layout && layout.dataset.jobsIndexUrl) || "/jobs/";

    const html =
      '<div id="job-detail" class="jobs-detail" data-job-id="' +
      escapeHtml(String(r)) +
      '" data-output-folder="' +
      escapeHtml(outFolder) +
      '">' +
      '<div class="p-4 border-bottom d-flex align-items-start justify-content-between">' +
      '<div class="flex-grow-1">' +
      '<h2 class="h5 mb-1">' +
      escapeHtml(job.title) +
      "</h2>" +
      '<p class="text-muted small mb-2">' +
      escapeHtml(job.employer) +
      " · " +
      escapeHtml(job.location) +
      "</p>" +
      '<a href="' +
      escapeHtml(job.listing_url) +
      '" target="_blank" rel="noopener" class="small text-decoration-none d-inline-flex align-items-center gap-1">View listing <i class="bi bi-box-arrow-up-right"></i></a></div>' +
      '<button type="button" class="btn btn-sm btn-link text-muted p-1" ' +
      'hx-get="' +
      escapeHtml(jobsIndexUrl) +
      '" hx-select="#job-detail" hx-target="#job-detail" hx-swap="outerHTML" ' +
      'onclick="document.querySelectorAll(\'#jobs-tbody tr.is-selected\').forEach(function(el){ el.classList.remove(\'is-selected\'); });">' +
      '<i class="bi bi-x-lg"></i></button></div>' +
      '<div class="flex-grow-1 overflow-auto p-4">' +
      buildDescriptionSection(job) +
      '<div id="job-cv-sections-placeholder" class="text-muted small py-3">Loading tailored CV…</div>' +
      "</div>" +
      buildActionRowSection(job, base) +
      "</div>";

    const holder = document.getElementById("job-detail");
    if (!holder) return;

    const wrap = document.createElement("div");
    wrap.innerHTML = html.trim();
    const detailEl = wrap.firstElementChild;
    if (!detailEl) return;

    holder.replaceWith(detailEl);

    if (window.htmx) {
      window.htmx.process(detailEl);
    }

    const cvUrl =
      base +
      "/" +
      encodeURIComponent(r) +
      "/cv-sections?output_folder=" +
      encodeURIComponent(outFolder);

    fetch(cvUrl, { credentials: "same-origin" })
      .then(function (res) {
        if (!res.ok) throw new Error("cv-sections");
        return res.text();
      })
      .then(function (fragment) {
        const ph = document.getElementById("job-cv-sections-placeholder");
        if (!ph) return;
        ph.outerHTML = fragment;
        if (window.htmx) {
          window.htmx.process(detailEl);
        }
      })
      .catch(function () {
        const ph = document.getElementById("job-cv-sections-placeholder");
        if (ph) {
          ph.innerHTML =
            '<span class="text-danger">Could not load CV panel. Refresh the page and try again.</span>';
        }
      });
  }

  document.addEventListener("click", function (event) {
    const tr = event.target.closest("#jobs-tbody tr.job-row");
    if (!tr || !tr.dataset || tr.dataset.jobJson == null) return;

    let job;
    try {
      job = JSON.parse(tr.dataset.jobJson);
    } catch (err) {
      return;
    }

    document
      .querySelectorAll("#jobs-tbody tr.is-selected")
      .forEach(function (el) {
        el.classList.remove("is-selected");
      });
    tr.classList.add("is-selected");

    const layout = document.querySelector(".jobs-layout");
    openJobDetail(job, layout);
  });

  document.addEventListener("keydown", function (event) {
    const isSaveCombo =
      (event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey &&
      (event.key === "s" || event.key === "S");
    if (!isSaveCombo) return;

    const active = document.activeElement;
    if (!active || !active.hasAttribute("data-cv-textarea")) return;

    event.preventDefault();
    const saveBtn = document.querySelector(
      '[data-cv-save-for="' + active.id + '"]'
    );
    if (saveBtn) saveBtn.click();
  });

  document.addEventListener("click", function (event) {
    const btn = event.target.closest(".js-reset-cv");
    if (!btn || btn.disabled) return;

    event.preventDefault();

    if (btn.dataset.confirming === "1") {
      clearResetConfirm(btn);
      const url = btn.dataset.resetUrl;
      if (!url || !window.htmx) return;
      const target = btn.dataset.resetTarget || "#job-detail";
      window.htmx.ajax("POST", url, {
        target: target,
        swap: "outerHTML",
        values: { output_folder: btn.dataset.outputFolder || "" },
      });
      return;
    }

    setResetConfirm(btn);
  });

  document.addEventListener("click", function (event) {
    if (event.target.closest(".js-reset-cv")) return;
    document
      .querySelectorAll('.js-reset-cv[data-confirming="1"]')
      .forEach(clearResetConfirm);
  });

  function setResetConfirm(btn) {
    btn.dataset.confirming = "1";
    btn.classList.add("is-confirming");
    btn.dataset.originalTitle = btn.getAttribute("title") || "";
    btn.setAttribute("title", "Click again to confirm");
    btn._resetTimer = window.setTimeout(function () {
      clearResetConfirm(btn);
    }, CONFIRM_WINDOW_MS);
  }

  function clearResetConfirm(btn) {
    if (btn._resetTimer) {
      window.clearTimeout(btn._resetTimer);
      btn._resetTimer = null;
    }
    btn.dataset.confirming = "0";
    btn.classList.remove("is-confirming");
    if (btn.dataset.originalTitle !== undefined) {
      btn.setAttribute("title", btn.dataset.originalTitle);
    }
  }

  function getJobIdFor(element) {
    const host = element.closest("[data-job-id]");
    return host ? host.dataset.jobId : null;
  }

  function refreshPreview(jobId, textarea) {
    if (!jobId) return;
    const iframe = document.getElementById("cv-preview-iframe-" + jobId);
    if (!iframe) return;
    const url = textarea && textarea.dataset.previewUrl;
    if (!url) return;

    const body = new URLSearchParams();
    body.set("json_text", textarea.value);

    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    })
      .then(function (r) { return r.text(); })
      .then(function (html) {
        iframe.srcdoc = html;
      })
      .catch(function () { /* ignore transient fetch failures */ });
  }

  document.addEventListener("input", function (event) {
    const target = event.target;
    if (!target || !target.matches || !target.matches("[data-cv-textarea]")) return;

    const jobId = getJobIdFor(target);
    if (!jobId) return;

    const existing = previewTimers.get(jobId);
    if (existing) window.clearTimeout(existing);
    previewTimers.set(
      jobId,
      window.setTimeout(function () {
        previewTimers.delete(jobId);
        refreshPreview(jobId, target);
      }, PREVIEW_DEBOUNCE_MS)
    );
  });

  document.addEventListener("click", function (event) {
    const btn = event.target.closest(".js-template-choice");
    if (!btn) return;

    event.preventDefault();

    const choice = btn.dataset.templateChoice;
    const url = btn.dataset.templateUrl;
    const jobId = getJobIdFor(btn);
    if (!choice || !url || !jobId) return;

    const group = document.getElementById("cv-template-buttons-" + jobId);
    const peers = group
      ? group.querySelectorAll(".js-template-choice")
      : [];
    peers.forEach(function (peer) {
      const isActive = peer === btn;
      peer.classList.toggle("btn-dark", isActive);
      peer.classList.toggle("btn-outline-secondary", !isActive);
      peer.setAttribute("aria-pressed", isActive ? "true" : "false");
    });

    const body = new URLSearchParams();
    body.set("template", choice);
    body.set("output_folder", btn.dataset.outputFolder || "");

    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    })
      .then(function (r) { return r.json().catch(function () { return null; }); })
      .then(function (data) {
        if (!data || !data.ok) return;
        const textarea = document.getElementById(
          "cv-json-textarea-" + jobId
        );
        if (textarea) refreshPreview(jobId, textarea);
      })
      .catch(function () { /* ignore */ });
  });

  window.addEventListener("message", function (event) {
    const payload = event.data;
    if (!payload || payload.type !== "cv-preview-overflow") return;
    const badge = document.getElementById(
      "cv-overflow-badge-" + payload.jobId
    );
    if (!badge) return;
    badge.classList.toggle("d-none", !payload.overflow);
  });

  document.body.addEventListener("htmx:afterSwap", function (event) {
    const target = event.target;
    if (!target || !target.classList || !target.classList.contains("cv-feedback")) {
      return;
    }
    if (!target.querySelector(".text-success")) return;

    target.classList.remove("is-fading");
    window.setTimeout(function () {
      target.classList.add("is-fading");
      window.setTimeout(function () {
        if (target.classList.contains("is-fading")) {
          target.innerHTML = "";
          target.classList.remove("is-fading");
        }
      }, 700);
    }, FADE_DELAY_MS);
  });

  document.body.addEventListener("htmx:afterSwap", function (event) {
    const target = event.target;
    if (!target || !target.id) return;
    const match = target.id.match(/^job-action-row-(\d+)$/);
    if (!match) return;
    const row = match[1];
    const statusCell = document.getElementById("job-row-status-" + row);
    if (!statusCell) return;
    const approvedBtn = target.querySelector('[title="Already approved"]');
    if (approvedBtn) {
      statusCell.innerHTML =
        '<span class="status-badge status-badge--approved">Approved</span>';
    }
  });
})();
