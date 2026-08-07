self.addEventListener("install", function () { self.skipWaiting(); });
self.addEventListener("activate", function (event) { event.waitUntil(self.clients.claim()); });

self.addEventListener("push", function (event) {
    var data = {};
    try { data = event.data ? event.data.json() : {}; } catch (_) { data = {}; }
    var title = data.title || "MÜYS Bildirimi";
    var options = {
        body: data.body || "Yeni bir bildiriminiz var.",
        icon: "/static/img/logo_menu.png",
        badge: "/static/img/logo_menu.png",
        data: {url: data.url || "/"},
        tag: data.url || "muys-notification",
        renotify: true,
    };
    event.waitUntil(Promise.all([
        self.registration.showNotification(title, options),
        data.badge && self.navigator.setAppBadge ? self.navigator.setAppBadge(Number(data.badge)) : Promise.resolve(),
    ]));
});

self.addEventListener("notificationclick", function (event) {
    event.notification.close();
    var target = new URL((event.notification.data && event.notification.data.url) || "/", self.location.origin).href;
    event.waitUntil(self.clients.matchAll({type: "window", includeUncontrolled: true}).then(function (clients) {
        var sameOrigin = clients.find(function (client) { return new URL(client.url).origin === self.location.origin; });
        if (sameOrigin) return sameOrigin.navigate(target).then(function () { return sameOrigin.focus(); });
        return self.clients.openWindow(target);
    }));
});

self.addEventListener("pushsubscriptionchange", function () {
    // Yeni abonelik anahtarı uygulama tekrar açıldığında sunucuya kaydedilir.
});
