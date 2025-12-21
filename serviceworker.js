self.addEventListener("push", function (event) {
    const data = event.data ? event.data.json() : {};

    self.registration.showNotification(
        data.title || "🚨 Emergency Alert",
        {
            body: data.body || "Emergency nearby!",
            icon: "/static/images/alert.png",
            badge: "/static/images/alert.png",
            vibrate: [500, 200, 500, 200, 800],
            requireInteraction: true,
            data: {
                url: "/notifications/"
            }
        }
    );
});

self.addEventListener("notificationclick", function (event) {
    event.notification.close();
    event.waitUntil(clients.openWindow(event.notification.data.url));
});
