// ================= GLOBAL LOCATION OBJECT =================
let userLocation = {
    lat: null,
    lon: null,
    address: null
};

// ================= NAVBAR =================
function toggleMenu() {
    document.getElementById("navLinks").classList.toggle("show");
}

// ================= OPEN ALERT FORM =================
function openAlertForm() {
    if (!document.body.innerHTML.includes("Logout")) {
        alert("⚠️ Please login to send emergency alerts.");
        return;
    }
    getLocation();
}

// ================= GET LOCATION =================
function getLocation() {
    const statusEl = document.getElementById("status");
    statusEl.innerText = "📡 Fetching location...";

    navigator.geolocation.getCurrentPosition(async pos => {
        userLocation.lat = pos.coords.latitude;
        userLocation.lon = pos.coords.longitude;

        const res = await fetch(`/reverse-geocode/?lat=${userLocation.lat}&lon=${userLocation.lon}`);
        const data = await res.json();

        userLocation.address = data.address;
        statusEl.innerText = "📍 Location: " + data.address;
        document.getElementById("alertModal").style.display = "flex";
    });
}

// ================= CLOSE MODAL =================
function closeAlertForm() {
    document.getElementById("alertModal").style.display = "none";
}

// ================= SUBMIT ALERT =================
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("alertForm");

    form.addEventListener("submit", e => {
        e.preventDefault();

        const fd = new FormData(form);
        fd.append("latitude", userLocation.lat);
        fd.append("longitude", userLocation.lon);
        fd.append("address", userLocation.address);

        fetch("/send-alert/", {
            method: "POST",
            headers: { "X-CSRFToken": getCookie("csrftoken") },
            body: fd
        })
        .then(r => r.json())
        .then(() => {
            alert("✅ Emergency alert sent!");
            closeAlertForm();
            form.reset();
        });
    });
});

// ================= CSRF =================
function getCookie(name) {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith(name + "="))
        ?.split("=")[1];
}

// ================= 🔔 EMERGENCY NOTIFICATION =================
let lastAlertId = null;

function showEmergencyNotification(title, message) {
    // Popup
    if (Notification.permission === "granted") {
        new Notification(title, {
            body: message,
            icon: "/static/images/alert.png"
        });
    }

    // Sound
    new Audio("/static/sounds/emergency.mp3").play().catch(()=>{});

    // Vibration
    if (navigator.vibrate) {
        navigator.vibrate([500, 200, 500, 200, 1000]);
    }
}

// ================= CHECK ALERTS =================
function checkForEmergencyAlerts() {
    fetch("/alerts/")
        .then(r => r.json())
        .then(data => {
            if (!data.alerts.length) return;

            const latest = data.alerts[0];
            if (lastAlertId !== latest.id) {
                lastAlertId = latest.id;
                showEmergencyNotification("🚨 Emergency Alert Nearby", latest.address);
            }
        });
}

// 🔁 Every 5 seconds
setInterval(checkForEmergencyAlerts, 5000);

// 🔐 Ask permission once
if ("Notification" in window && Notification.permission !== "granted") {
    Notification.requestPermission();
}
navigator.geolocation.getCurrentPosition(pos => {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;

    fetch(`/nearby-services/?lat=${lat}&lon=${lon}`)
        .then(res => res.json())
        .then(data => {
            console.log("Nearby Services:", data.services);
        });
});
