document.addEventListener("DOMContentLoaded", () => {


    const current = window.location.pathname;


    // ==================================
    // AKTİF MENÜ
    // ==================================

    document.querySelectorAll(".sidebar a").forEach(link => {


        const href = link.getAttribute("href");


        if (!href || href.startsWith("#")) {
            return;
        }


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



    // ==================================
    // MOBİL SIDEBAR
    // ==================================

    const sidebar = document.getElementById("sidebar");

    const menuToggle = document.getElementById("menuToggle");


    if (sidebar && menuToggle) {


        menuToggle.addEventListener("click", (e) => {


            e.stopPropagation();


            sidebar.classList.toggle("show");


        });



        document.addEventListener("click", (e) => {


            if (window.innerWidth < 992) {


                if (
                    !sidebar.contains(e.target) &&
                    !menuToggle.contains(e.target)
                ) {


                    sidebar.classList.remove("show");


                }


            }


        });



    }





    // ==================================
    // STOK ALT MENÜ OTOMATİK AÇILMA
    // ==================================

    const stokMenu = document.getElementById("stokMenu");


    if (stokMenu) {


        if (
            current.startsWith("/urunler") ||
            current.startsWith("/receteler")
        ) {


            const collapse = new bootstrap.Collapse(
                stokMenu,
                {
                    toggle:true
                }
            );


        }


    }



});