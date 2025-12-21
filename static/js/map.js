// ================= MAP INITIALIZATION =================
let map = L.map("map").setView([17.385044, 78.486671], 13); // Default: Hyderabad

// ================= TILE LAYER =================
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors"
}).addTo(map);

// ================= MARKER STORAGE =================
let userMarkers = {};
let alertMarkers = [];
let serviceMarkers = [];

// ================= ICONS =================

// 👤 User icon
const userIcon = L.icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
    iconSize: [32, 32],
    iconAnchor: [16, 32]
});

// 🚨 Alert icon
const alertIcon = L.icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
    iconSize: [32, 32],
    iconAnchor: [16, 32]
});

// 🚓 Police marker (emoji)
const policeIcon = L.divIcon({
    html: "🚓",
    className: "",
    iconSize: [30, 30]
});

// 🏥 Hospital marker (emoji)
const hospitalIcon = L.divIcon({
    html: "🏥",
    className: "",
    iconSize: [30, 30]
});


// ================= LIVE USER LOCATIONS =================
function fetchLocations() {
    fetch("/live-locations/")
        .then(res => res.json())
        .then(data => {
            data.locations.forEach(user => {
                const latlng = [user.latitude, user.longitude];

                if (userMarkers[user.username]) {
                    userMarkers[user.username].setLatLng(latlng);
                } else {
                    userMarkers[user.username] = L.marker(latlng, {
                        icon: userIcon
                    })
                    .addTo(map)
                    .bindPopup(`👤 <b>${user.username}</b>`);
                }
            });
        })
        .catch(err => console.error("User location error:", err));
}

// ================= EMERGENCY ALERTS =================
function fetchAlerts() {
    fetch("/alerts/")
        .then(res => res.json())
        .then(data => {
            alertMarkers.forEach(marker => map.removeLayer(marker));
            alertMarkers = [];

            data.alerts.forEach(alert => {
                const marker = L.marker(
                    [alert.latitude, alert.longitude],
                    { icon: alertIcon }
                )
                .addTo(map)
                .bindPopup(`
                    🚨 <b>Emergency Alert</b><br>
                    ${alert.address}
                `);

                alertMarkers.push(marker);
            });
        })
        .catch(err => console.error("Alert fetch error:", err));
}

// ================= NEARBY POLICE & HOSPITALS =================
function fetchNearbyServices(lat, lon) {
    fetch(`/nearby-services/?lat=${lat}&lon=${lon}`)
        .then(res => res.json())
        .then(data => {
            serviceMarkers.forEach(m => map.removeLayer(m));
            serviceMarkers = [];

            data.services.forEach(service => {
                const icon =
                    service.type === "police" ? policeIcon : hospitalIcon;

                const marker = L.marker(
                    [service.latitude, service.longitude],
                    { icon: icon }
                )
                .addTo(map)
                .bindPopup(`
                    ${service.type === "police" ? "🚓" : "🏥"}
                    <b>${service.name}</b><br>
                    ${service.address || "Address not available"}
                `);

                serviceMarkers.push(marker);
            });
        })
        .catch(err => console.error("Nearby services error:", err));
}

// ================= USER GEOLOCATION =================
navigator.geolocation.getCurrentPosition(
    position => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        // Center map on user
        map.setView([lat, lon], 14);

        // User marker
        L.marker([lat, lon])
            .addTo(map)
            .bindPopup("📍 You are here")
            .openPopup();

        // Fetch nearby police & hospitals
        fetchNearbyServices(lat, lon);
    },
    () => {
        alert("Location permission is required to show nearby services.");
    }
);

// ================= INITIAL LOAD =================
fetchLocations();
fetchAlerts();

// ================= AUTO REFRESH =================
setInterval(fetchLocations, 30000);  // users every 30s
setInterval(fetchAlerts, 15000);     // alerts every 15s
