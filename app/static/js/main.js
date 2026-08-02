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


            sidebar.classList.toggle("show");


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