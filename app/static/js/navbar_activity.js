document.addEventListener("DOMContentLoaded", function () {
    const liveActivity = document.getElementById("liveActivity");
    const liveActivityText = document.getElementById("liveActivityText");
    let liveActivityTimer = null;
    let sonLogKimligi = null;

    if (!liveActivity || !liveActivityText) return;

    function canliHareketiGoster(hareketler) {
        if (!liveActivity || !liveActivityText) return;
        const sonHareket = hareketler.length ? hareketler[0] : null;
        if (!sonHareket) return;
        const yeniKimlik = Number(sonHareket.id || 0);
        if (sonLogKimligi === null) { sonLogKimligi = yeniKimlik; return; }
        if (yeniKimlik <= sonLogKimligi) return;
        sonLogKimligi = yeniKimlik;
        if (liveActivityTimer) window.clearTimeout(liveActivityTimer);
        liveActivityText.textContent = sonHareket.kullanici_adi + " · " + sonHareket.islem + " · " + sonHareket.zaman;
        liveActivity.title = liveActivityText.textContent;
        liveActivity.classList.remove("d-none");
        liveActivityTimer = window.setTimeout(function () {
            liveActivity.classList.add("d-none");
            liveActivityText.textContent = "";
        }, 8000);
    }

    function sonHareketleriYukle() {
        fetch("/api/islem-loglari/son", {headers: {"Accept": "application/json"}})
            .then(function (response) { return response.ok ? response.json() : {hareketler: []}; })
            .then(function (veri) {
                const hareketler = veri.hareketler || [];
                canliHareketiGoster(hareketler);
            })
            .catch(function () {
                canliHareketiGoster([]);
            });
    }

    sonHareketleriYukle();
    window.setInterval(sonHareketleriYukle, 5000);
});
