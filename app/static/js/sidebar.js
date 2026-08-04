document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");

    menuToggle?.addEventListener("click", (event) => {
        event.stopPropagation();
        sidebar?.classList.toggle("show");
    });

    document.addEventListener("click", (event) => {
        if (window.innerWidth <= 991 && sidebar?.classList.contains("show")
            && !sidebar.contains(event.target) && !menuToggle?.contains(event.target)
            ) {
            sidebar.classList.remove("show");
        }
    });

    const current = window.location.pathname;
    document.querySelectorAll(".sidebar a").forEach((link) => {
        const href = link.getAttribute("href");
        if (!href || href.startsWith("#")) return;
        link.classList.toggle("active", href === "/" ? current === "/" : current === href || current.startsWith(`${href}/`));
        link.addEventListener("click", () => {
            if (window.innerWidth <= 991 && link.getAttribute("data-bs-toggle") !== "collapse") sidebar?.classList.remove("show");
        });
    });

    const stokMenu = document.getElementById("stokMenu");
    if (stokMenu && (current.startsWith("/urunler") || current.startsWith("/receteler"))) {
        new bootstrap.Collapse(stokMenu, { toggle: true });
    }
});
