document.addEventListener("DOMContentLoaded", function () {
    const activityFeed = document.getElementById("activityFeed");
    const activityBadge = document.getElementById("activityBadge");
    const liveActivity = document.getElementById("liveActivity");
    const liveActivityText = document.getElementById("liveActivityText");
    let liveActivityTimer = null;

    if (!activityFeed) return;

    function metniGuvenliYaz(metin) {
        const kapsayici = document.createElement("div");
        kapsayici.textContent = metin || "";
        return kapsayici.innerHTML;
    }

    function hareketleriGoster(hareketler) {
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
        fetch("/api/islem-loglari/son", {headers: {"Accept": "application/json"}})
            .then(function (response) { return response.ok ? response.json() : {hareketler: []}; })
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
    window.setInterval(sonHareketleriYukle, 5000);
});
