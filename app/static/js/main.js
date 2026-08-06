document.addEventListener("DOMContentLoaded", function () {


    const current = window.location.pathname;



    // ==========================
    // AKTİF MENÜ
    // ==========================

    document.querySelectorAll(".sidebar a").forEach(function(link){


        const href = link.getAttribute("href");


        if(!href || href.startsWith("#")){
            return;
        }


        link.classList.remove("active");


        if(href === "/"){


            if(current === "/"){

                link.classList.add("active");

            }


        } else {


            if(
                current === href ||
                current.startsWith(href + "/")
            ){

                link.classList.add("active");

            }


        }


    });





    // ==========================
    // MOBİL SIDEBAR
    // ==========================


    const sidebar = document.getElementById("sidebar");

    const menuToggle = document.getElementById("menuToggle");



    if(sidebar && menuToggle){



        menuToggle.addEventListener("click", function(e){


            e.stopPropagation();


            if (window.innerWidth <= 991) {
                sidebar.classList.toggle("show");
            } else {
                document.body.classList.toggle("sidebar-collapsed");
            }


        });





        document.addEventListener("click", function(e){


            if(window.innerWidth <= 991){



                if(
                    sidebar.classList.contains("show") &&
                    !sidebar.contains(e.target) &&
                    !menuToggle.contains(e.target)
                ){


                    sidebar.classList.remove("show");


                }


            }


        });





        // Link tıklayınca kapat
        // fakat dropdown açan stok menüsünde kapatma


        sidebar.querySelectorAll("a").forEach(function(link){


            link.addEventListener("click",function(){



                if(
                    link.getAttribute("data-bs-toggle") === "collapse"
                ){

                    return;

                }



                if(window.innerWidth <= 991){


                    sidebar.classList.remove("show");


                }



            });



        });



    }

    // ==========================
    // SAYFA GERİ DÖNÜŞÜ
    // ==========================

    document.querySelectorAll("[data-page-back]").forEach(function (button) {
        button.addEventListener("click", function (event) {
            const fallbackUrl = button.getAttribute("href") || "/";
            const sameSiteReferrer = document.referrer && new URL(document.referrer).origin === window.location.origin;

            if (sameSiteReferrer && window.history.length > 1) {
                event.preventDefault();
                window.history.back();
            } else {
                button.setAttribute("href", fallbackUrl);
            }
        });
    });

    // ==========================
    // STOK MENÜ OTOMATİK AÇ
    // ==========================


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
