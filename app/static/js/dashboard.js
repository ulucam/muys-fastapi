document.addEventListener("DOMContentLoaded", () => {
    const buttons = [...document.querySelectorAll("[data-dashboard-target]")];
    const panels = [...document.querySelectorAll("[data-dashboard-panel]")];

    if (!buttons.length || !panels.length) return;

    const panelMatches = (panel, target) =>
        (panel.dataset.dashboardPanel || "").split(/\s+/).includes(target);

    const showPanel = (target, updateHash = true) => {
        buttons.forEach((button) => {
            const active = button.dataset.dashboardTarget === target;
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-pressed", String(active));
        });

        panels.forEach((panel) => {
            const active = panelMatches(panel, target);
            panel.hidden = !active;
            panel.classList.toggle("is-active", active);
        });

        if (target === "teslim") {
            const teslimAccordion = document.querySelector("#icerik-3");
            if (teslimAccordion && window.bootstrap) {
                window.bootstrap.Collapse.getOrCreateInstance(teslimAccordion, { toggle: false }).show();
            }
        }

        if (updateHash) history.replaceState(null, "", `#dashboard-${target}`);
    };

    buttons.forEach((button) => {
        button.addEventListener("click", () => showPanel(button.dataset.dashboardTarget));
    });

    const hashTarget = location.hash.replace("#dashboard-", "");
    const legacyTargets = {
        "siparisler": "siparisler",
        "siparis-onay": "siparisler",
        "uretim-paneli": "uretim",
        "devamsizPanel": "devamsiz",
        "siparis-3": "teslim",
    };
    const initialTarget = buttons.some((button) => button.dataset.dashboardTarget === hashTarget)
        ? hashTarget
        : legacyTargets[location.hash.slice(1)] || "uretim";

    showPanel(initialTarget, false);
});
