document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-module-workspace]").forEach((workspace) => {
        const toolbar = workspace.querySelector(".module-toolbar");
        const dockToggle = workspace.querySelector("[data-module-dock-toggle]");
        const buttons = [...workspace.querySelectorAll("[data-module-target]")];
        const panels = [...workspace.querySelectorAll("[data-module-panel]")];

        const setDockOpen = (open) => {
            if (!toolbar || !dockToggle) return;
            toolbar.classList.toggle("is-open", open);
            dockToggle.setAttribute("aria-expanded", String(open));
            dockToggle.setAttribute("aria-label", `${toolbar.getAttribute("aria-label") || "Bölüm"} menüsünü ${open ? "kapat" : "aç"}`);
            const icon = dockToggle.querySelector("i");
            if (icon) icon.className = `bi ${open ? "bi-chevron-right" : "bi-chevron-left"}`;
        };

        if (dockToggle) {
            dockToggle.addEventListener("click", () => setDockOpen(!toolbar.classList.contains("is-open")));
            setDockOpen(false);
        }

        if (!buttons.length || !panels.length) return;

        const showPanel = (target, updateHash = true) => {
            buttons.forEach((button) => {
                const active = button.dataset.moduleTarget === target;
                button.classList.toggle("is-active", active);
                button.setAttribute("aria-pressed", String(active));
            });
            panels.forEach((panel) => {
                const active = (panel.dataset.modulePanel || "").split(/\s+/).includes(target);
                panel.hidden = !active;
                panel.classList.toggle("is-active", active);
            });
            if (updateHash) history.replaceState(null, "", `#module-${target}`);
        };

        buttons.forEach((button) => button.addEventListener("click", () => showPanel(button.dataset.moduleTarget)));
        const requested = location.hash.replace("#module-", "");
        const initial = buttons.some((button) => button.dataset.moduleTarget === requested)
            ? requested
            : (buttons.find((button) => button.classList.contains("is-active")) || buttons[0]).dataset.moduleTarget;
        showPanel(initial, false);
    });
});
