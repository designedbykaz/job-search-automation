(function () {
  "use strict";

  const CONFIRM_WINDOW_MS = 3000;
  const FADE_DELAY_MS = 2500;
  const PREVIEW_DEBOUNCE_MS = 400;

  const previewTimers = new Map();

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
      window.htmx.ajax("POST", url, {
        target: "#job-detail",
        swap: "outerHTML",
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
})();
