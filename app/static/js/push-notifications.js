document.addEventListener("DOMContentLoaded", function () {
    const button = document.getElementById("pushToggle");
    const status = document.getElementById("pushStatus");
    if (!button || !status) return;

    let publicKey = "";
    let registration = null;
    let subscription = null;
    const supported = window.isSecureContext && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
    const iosNeedsInstall = /iPhone|iPad|iPod/.test(navigator.userAgent) && !window.matchMedia("(display-mode: standalone)").matches;

    function base64Key(value) {
        const padding = "=".repeat((4 - value.length % 4) % 4);
        const raw = atob((value + padding).replace(/-/g, "+").replace(/_/g, "/"));
        return Uint8Array.from(raw, function (char) { return char.charCodeAt(0); });
    }
    function deviceName() {
        return [navigator.platform || "", navigator.userAgent || ""].filter(Boolean).join(" ").slice(0, 200);
    }
    function render() {
        button.disabled = !supported || !publicKey || iosNeedsInstall;
        button.textContent = subscription ? "Kapat" : "Bildirimleri Aç";
        button.classList.toggle("btn-outline-danger", Boolean(subscription));
        button.classList.toggle("btn-outline-primary", !subscription);
        if (!supported) status.textContent = "Bu tarayıcı veya bağlantı desteklemiyor.";
        else if (!publicKey) status.textContent = "Sunucu VAPID anahtarları bekleniyor.";
        else if (subscription) status.textContent = "Bu cihazda bildirimler açık.";
        else if (iosNeedsInstall) status.textContent = "iPhone'da önce Ana Ekrana Ekle ile kurun.";
        else status.textContent = "Bu cihazda bildirimler kapalı.";
    }
    async function saveSubscription(value) {
        const response = await fetch("/api/push/abone-ol", {
            method: "POST", headers: {"Content-Type": "application/json", "X-Requested-With": "MUYS-PWA"},
            body: JSON.stringify({subscription: value.toJSON(), cihaz_adi: deviceName()}),
        });
        if (!response.ok) throw new Error("Abonelik kaydedilemedi");
    }
    async function enable() {
        const permission = await Notification.requestPermission();
        if (permission !== "granted") throw new Error("Bildirim izni verilmedi");
        subscription = await registration.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: base64Key(publicKey)});
        try { await saveSubscription(subscription); }
        catch (error) { await subscription.unsubscribe(); subscription = null; throw error; }
    }
    async function disable() {
        const endpoint = subscription.endpoint;
        await fetch("/api/push/abonelikten-cik", {
            method: "POST", headers: {"Content-Type": "application/json", "X-Requested-With": "MUYS-PWA"},
            body: JSON.stringify({endpoint: endpoint}),
        });
        await subscription.unsubscribe();
        subscription = null;
    }
    async function initialize() {
        if (!supported) { render(); return; }
        const response = await fetch("/api/push/durum", {headers: {"Accept": "application/json"}});
        if (!response.ok) return;
        const data = await response.json();
        publicKey = data.public_key || "";
        registration = await navigator.serviceWorker.register("/sw.js", {scope: "/"});
        subscription = await registration.pushManager.getSubscription();
        if (subscription && publicKey) await saveSubscription(subscription).catch(function () {});
        render();
    }
    button.addEventListener("click", async function () {
        button.disabled = true;
        status.textContent = "İşlem yapılıyor...";
        try { if (subscription) await disable(); else await enable(); }
        catch (error) { status.textContent = error.message || "Bildirim ayarı değiştirilemedi."; }
        finally { render(); }
    });
    initialize().catch(function () { status.textContent = "Bildirim durumu alınamadı."; });
});
