document.addEventListener("DOMContentLoaded", function () {
    const feed = document.getElementById("notificationFeed");
    const notificationBadge = document.getElementById("notificationBadge");
    const messageBadge = document.getElementById("messageBadge");
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
        badge(messageBadge, Number(data.okunmamis_mesaj || 0));
        const items = data.bildirimler || [];
        feed.innerHTML = items.length ? items.map(function (item) {
            const content = '<div class="activity-item ' + (!item.okundu ? 'notification-item-unread' : '') + '">' +
                '<div class="activity-item-icon"><i class="bi ' + (item.tur === 'mesaj' ? 'bi-chat-dots' : 'bi-info-circle') + '"></i></div>' +
                '<div class="activity-item-body"><div class="activity-item-title"><strong>' + safe(item.baslik) + '</strong></div>' +
                '<div class="activity-item-meta">' + safe(item.mesaj) + '</div><div class="activity-item-meta">' + safe(item.zaman) + '</div></div></div>';
            return item.baglanti ? '<a class="notification-item-link" href="' + safe(item.baglanti) + '">' + content + '</a>' : content;
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
    document.addEventListener("visibilitychange", load);
    load();
    window.setInterval(load, 15000);
});
