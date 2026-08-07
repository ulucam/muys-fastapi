document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-module-workspace]").forEach((workspace) => {
        const buttons = [...workspace.querySelectorAll("[data-module-target]")];
        const panels = [...workspace.querySelectorAll("[data-module-panel]")];
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
