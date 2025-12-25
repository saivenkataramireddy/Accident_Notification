// ================= GLOBAL LOCATION OBJECT =================
let userLocation = {
    lat: null,
    lon: null,
    address: null
};

let emergencyType = null;
let countdownTimer = null;
let timeLeft = 10;

// ================= CSRF =================
function getCookie(name) {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith(name + "="))
        ?.split("=")[1];
}

// ================= NAVBAR =================
function toggleMenu() {
    document.getElementById("navLinks").classList.toggle("show");
}

// ================= SAVE USER LOCATION (ON LOAD) =================
document.addEventListener("DOMContentLoaded", () => {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(
        pos => {
            fetch("/update-location/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({
                    lat: pos.coords.latitude,
                    lon: pos.coords.longitude
                })
            })
            .then(res => res.json())
            .then(data => {
                console.log("📍 Location saved:", data);
            });
        },
        err => {
            console.warn("⚠️ Location permission denied");
        }
    );
});

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

        const res = await fetch(
            `/reverse-geocode/?lat=${userLocation.lat}&lon=${userLocation.lon}`
        );
        const data = await res.json();

        userLocation.address = data.address;
        statusEl.innerText = "📍 Location: " + data.address;

        document.getElementById("whoModal").style.display = "flex";
        startCountdown();
    });
}

// ================= CLOSE MODALS =================
function closeAlertForm() {
    document.getElementById("alertModal").style.display = "none";
}

// ================= COUNTDOWN =================
function startCountdown() {
    timeLeft = 10;
    document.getElementById("countdown").innerText = timeLeft;

    countdownTimer = setInterval(() => {
        timeLeft--;
        document.getElementById("countdown").innerText = timeLeft;

        if (timeLeft <= 0) {
            clearInterval(countdownTimer);
            chooseSelf(true); // auto submit
        }
    }, 1000);
}

// ================= USER CHOICE =================
function chooseSelf(auto = false) {
    clearInterval(countdownTimer);
    emergencyType = "self";
    document.getElementById("whoModal").style.display = "none";

    if (auto) {
        autoSubmitAlert();
    } else {
        document.getElementById("alertModal").style.display = "flex";
    }
}

function chooseOther() {
    clearInterval(countdownTimer);
    emergencyType = "other";
    document.getElementById("whoModal").style.display = "none";
    autoSubmitAlert();
}

// ================= AUTO SUBMIT ALERT =================
function autoSubmitAlert() {
    const fd = new FormData();
    fd.append("latitude", userLocation.lat);
    fd.append("longitude", userLocation.lon);
    fd.append("address", userLocation.address);
    fd.append(
        "description",
        emergencyType === "self"
            ? "User unable to respond – SELF emergency auto triggered"
            : "Accident reported for OTHER person"
    );

    fetch("/send-alert/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: fd
    })
    .then(res => res.json())
    .then(() => {
        alert("🚨 Emergency alert sent successfully!");
    })
    .catch(() => {
        alert("❌ Failed to send emergency alert");
    });
}

// ================= MANUAL FORM SUBMIT =================
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("alertForm");
    if (!form) return;

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

// ================= EMERGENCY NOTIFICATION =================
let lastAlertId = null;

function showEmergencyNotification(title, message) {
    if (Notification.permission === "granted") {
        new Notification(title, {
            body: message,
            icon: "/static/images/alert.png"
        });
    }

    new Audio("/static/sounds/emergency.mp3").play().catch(() => {});

    if (navigator.vibrate) {
        navigator.vibrate([500, 200, 500, 200, 1000]);
    }
}

// ================= POLL ALERTS =================
function checkForEmergencyAlerts() {
    fetch("/alerts/")
        .then(r => r.json())
        .then(data => {
            if (!data.alerts?.length) return;

            const latest = data.alerts[0];
            if (lastAlertId !== latest.id) {
                lastAlertId = latest.id;
                showEmergencyNotification(
                    "🚨 Emergency Alert Nearby",
                    latest.address
                );
            }
        });
}

setInterval(checkForEmergencyAlerts, 5000);

// ================= NOTIFICATION PERMISSION =================
if ("Notification" in window && Notification.permission !== "granted") {
    Notification.requestPermission();
}

// ================= NEARBY SERVICES =================
navigator.geolocation.getCurrentPosition(pos => {
    fetch(
        `/nearby-services/?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`
    )
    .then(res => res.json())
    .then(data => {
        console.log("🏥 Nearby Services:", data.services);
    });
});
