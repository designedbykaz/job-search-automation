(function () {
  "use strict";

  const CONFIRM_WINDOW_MS = 3000;
  const FADE_DELAY_MS = 2500;

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
