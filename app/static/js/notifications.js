document.addEventListener("DOMContentLoaded", function () {
    const feed = document.getElementById("notificationFeed");
    const notificationBadge = document.getElementById("notificationBadge");
    const markRead = document.getElementById("markNotificationsRead");
    if (!feed) return;

    function safe(value) {
        const node = document.createElement("span");
        node.textContent = value == null ? "" : String(value);
        return node.innerHTML;
    }
    function badge(node, count) {
        if (!node) return;
        node.textContent = count > 99 ? "99+" : count;
        node.classList.toggle("d-none", !count);
    }
    function render(data) {
        badge(notificationBadge, Number(data.okunmamis_bildirim || 0));
        if ("setAppBadge" in navigator) {
            const total = Number(data.okunmamis_bildirim || 0);
            if (total) navigator.setAppBadge(total).catch(function () {});
            else if ("clearAppBadge" in navigator) navigator.clearAppBadge().catch(function () {});
        }
        const items = data.bildirimler || [];
        feed.innerHTML = items.length ? items.map(function (item) {
            const content = '<div class="activity-item ' + (!item.okundu ? 'notification-item-unread' : '') + '">' +
                '<div class="activity-item-icon"><i class="bi ' + (item.tur === 'mesaj' ? 'bi-chat-dots' : 'bi-info-circle') + '"></i></div>' +
                '<div class="activity-item-body"><div class="activity-item-title"><strong>' + safe(item.baslik) + '</strong></div>' +
                '<div class="activity-item-meta">' + safe(item.mesaj) + '</div><div class="activity-item-meta">' + safe(item.zaman) + '</div></div></div>';
            return item.baglanti ? '<a class="notification-item-link" data-notification-id="' + Number(item.id) + '" href="' + safe(item.baglanti) + '">' + content + '</a>' : content;
        }).join("") : '<div class="activity-empty">Henüz bildiriminiz yok.</div>';
    }
    function load() {
        if (document.visibilityState !== "visible") return;
        fetch("/api/iletisim/ozet", {headers: {"Accept": "application/json"}})
            .then(function (response) { return response.ok ? response.json() : Promise.reject(); })
            .then(render).catch(function () {});
    }
    if (markRead) markRead.addEventListener("click", function () {
        fetch("/api/bildirimler/okundu", {method: "POST", headers: {"Accept": "application/json"}}).then(load);
    });
    feed.addEventListener("click", function (event) {
        const link = event.target.closest("[data-notification-id]");
        if (!link) return;
        event.preventDefault();
        const hedef = link.href;
        fetch("/api/bildirimler/" + link.dataset.notificationId + "/okundu", {method: "POST", headers: {"Accept": "application/json"}})
            .catch(function () {})
            .finally(function () { window.location.href = hedef; });
    });
    document.addEventListener("visibilitychange", load);
    document.addEventListener("muys:notifications-refresh", load);
    load();
    window.setInterval(load, 15000);
});
