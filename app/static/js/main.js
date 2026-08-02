document.addEventListener("DOMContentLoaded", () => {

    const current = window.location.pathname;

    document.querySelectorAll(".sidebar .nav-link").forEach(link => {

        const href = link.getAttribute("href");

        if (!href) return;

        link.classList.remove("active");

        if (href === "/") {

            if (current === "/") {

                link.classList.add("active");

            }

        } else {

            if (current === href || current.startsWith(href + "/")) {

                link.classList.add("active");

            }

        }

    });

});