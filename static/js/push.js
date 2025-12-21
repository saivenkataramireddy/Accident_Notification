if ("serviceWorker" in navigator && "PushManager" in window) {
    navigator.serviceWorker.register("/static/js/sw.js")
        .then(reg => {
            console.log("Service Worker Registered");
        });
}
