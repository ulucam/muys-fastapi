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
    // MOBİL SIDEBAR AÇ / KAPA
    // ==================================

    const sidebar = document.getElementById("sidebar");

    const menuToggle = document.getElementById("menuToggle");



    if (sidebar && menuToggle) {



        menuToggle.addEventListener("click", (e) => {


            e.stopPropagation();

            sidebar.classList.toggle("show");


        });



        document.addEventListener("click", (e) => {


            if(window.innerWidth < 992 &&
               sidebar.classList.contains("show")){


                const sidebarClick =
                    sidebar.contains(e.target);


                const buttonClick =
                    menuToggle.contains(e.target);



                if(!sidebarClick && !buttonClick){


                    sidebar.classList.remove("show");


                }


            }


        });



        // Menü linkine basınca mobilde kapat

        sidebar.querySelectorAll("a").forEach(link => {


            link.addEventListener("click", () => {


                if(window.innerWidth < 992){


                    sidebar.classList.remove("show");


                }


            });


        });


    }




    // ==================================
    // STOK MENÜSÜ OTOMATİK AÇ
    // ==================================

    const stokMenu = document.getElementById("stokMenu");


    if(stokMenu){


        if(
            current.startsWith("/urunler") ||
            current.startsWith("/receteler")
        ){


            new bootstrap.Collapse(
                stokMenu,
                {
                    toggle:true
                }
            );


        }


    }



});