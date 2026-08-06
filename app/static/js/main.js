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
    // SON KULLANICI HAREKETLERİ
    // ==========================

    const activityFeed = document.getElementById("activityFeed");
    const activityBadge = document.getElementById("activityBadge");
    const liveActivity = document.getElementById("liveActivity");
    const liveActivityText = document.getElementById("liveActivityText");
    let liveActivityTimer = null;

    function metniGuvenliYaz(metin) {
        const kapsayici = document.createElement("div");
        kapsayici.textContent = metin || "";
        return kapsayici.innerHTML;
    }

    function hareketleriGoster(hareketler) {
        if (!activityFeed) return;

        if (!hareketler.length) {
            activityFeed.innerHTML = '<div class="activity-empty">Henüz hareket bulunmuyor.</div>';
            if (activityBadge) activityBadge.classList.add("d-none");
            return;
        }

        activityFeed.innerHTML = hareketler.map(function (hareket) {
            return '<div class="activity-item">' +
                '<div class="activity-item-icon"><i class="bi bi-activity"></i></div>' +
                '<div class="activity-item-body">' +
                '<div class="activity-item-title"><strong>' + metniGuvenliYaz(hareket.kullanici_adi) + '</strong> · ' + metniGuvenliYaz(hareket.islem) + '</div>' +
                '<div class="activity-item-meta">' + metniGuvenliYaz(hareket.rol) + ' · ' + metniGuvenliYaz(hareket.modul) + ' · ' + metniGuvenliYaz(hareket.zaman) + '</div>' +
                '</div></div>';
        }).join("");

        if (activityBadge) {
            activityBadge.textContent = hareketler.length;
            activityBadge.classList.remove("d-none");
        }
    }

    function canliHareketiGoster(hareketler) {
        if (!liveActivity || !liveActivityText) return;
        if (liveActivityTimer) window.clearTimeout(liveActivityTimer);
        const sonHareket = hareketler.length ? hareketler[0] : null;
        if (!sonHareket || Number(sonHareket.yas_saniye) >= 60) {
            liveActivity.classList.add("d-none");
            liveActivityText.textContent = "";
            return;
        }
        liveActivityText.textContent = sonHareket.kullanici_adi + " · " + sonHareket.islem + " · " + sonHareket.zaman;
        liveActivity.title = liveActivityText.textContent;
        liveActivity.classList.remove("d-none");
        liveActivityTimer = window.setTimeout(function () {
            liveActivity.classList.add("d-none");
            liveActivityText.textContent = "";
        }, Math.max(0, 60 - Number(sonHareket.yas_saniye)) * 1000);
    }

    function sonHareketleriYukle() {
        if (!activityFeed) return;
        fetch("/api/islem-loglari/son", { headers: { "Accept": "application/json" } })
            .then(function (response) { return response.ok ? response.json() : { hareketler: [] }; })
            .then(function (veri) {
                const hareketler = veri.hareketler || [];
                hareketleriGoster(hareketler);
                canliHareketiGoster(hareketler);
            })
            .catch(function () {
                hareketleriGoster([]);
                canliHareketiGoster([]);
            });
    }

    sonHareketleriYukle();
    if (activityFeed) window.setInterval(sonHareketleriYukle, 5000);





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
