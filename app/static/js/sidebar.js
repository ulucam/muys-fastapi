document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");

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
