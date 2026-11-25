document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        if (!window.confirm(form.dataset.confirm)) {
            event.preventDefault();
        }
    });
});

document.querySelectorAll(".route-map").forEach((container) => {
    if (typeof L === "undefined") return;
    const latitude = Number(container.dataset.lat);
    const longitude = Number(container.dataset.lng);
    const routeMap = L.map(container, {
        attributionControl: false,
        zoomControl: false,
        dragging: false,
        scrollWheelZoom: false,
        doubleClickZoom: false,
    }).setView([latitude, longitude], 15);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
    }).addTo(routeMap);
    const route = [
        [latitude - 0.0018, longitude - 0.0022],
        [latitude - 0.0011, longitude - 0.0008],
        [latitude, longitude],
        [latitude + 0.0011, longitude + 0.0015],
        [latitude + 0.0020, longitude + 0.0028],
    ];
    L.polyline(route, { color: "#168d91", weight: 5 }).addTo(routeMap);
    L.circleMarker(route[0], { radius: 5, color: "#172f4a" }).addTo(routeMap);
    L.circleMarker(route[route.length - 1], { radius: 5, color: "#168d91" }).addTo(routeMap);
});

const vehicleLocationMap = document.querySelector("#vehicle-location-map");
function initializeLocationMap(container) {
    if (typeof L === "undefined") return;
    const latitude = Number(container.dataset.lat);
    const longitude = Number(container.dataset.lng);
    const locationMap = L.map(container).setView([latitude, longitude], 16);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap",
    }).addTo(locationMap);
    L.marker([latitude, longitude]).addTo(locationMap);
    window.setTimeout(() => locationMap.invalidateSize(), 100);
}
if (vehicleLocationMap) initializeLocationMap(vehicleLocationMap);

document.querySelectorAll(".activity-map").forEach((activityMap) => {
    if (typeof L === "undefined") return;
    const latitude = Number(activityMap.dataset.lat);
    const longitude = Number(activityMap.dataset.lng);
    const map = L.map(activityMap).setView([latitude, longitude], 15);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap",
    }).addTo(map);
    L.marker([latitude, longitude]).addTo(map);
    window.setTimeout(() => map.invalidateSize(), 100);
});

document.querySelectorAll("[data-ride-seconds]").forEach((rideDuration) => {
    let elapsedSeconds = Number(rideDuration.dataset.rideSeconds);
    const panel = rideDuration.closest(".active-ride-panel");
    const liveCost = panel.querySelector("[data-live-cost]");
    const liveDistance = panel.querySelector("[data-live-distance]");
    const startFee = Number(liveCost.dataset.startFee);
    const ratePerMinute = Number(liveCost.dataset.ratePerMinute);
    const vehicleId = Number(liveDistance.dataset.vehicleId);
    const updateRideStats = () => {
        const billedMinutes = Math.max(1, Math.ceil(elapsedSeconds / 60));
        const minutes = Math.floor(elapsedSeconds / 60);
        const seconds = elapsedSeconds % 60;
        rideDuration.textContent = `${minutes}:${String(seconds).padStart(2, "0")}`;
        liveCost.textContent = `${(startFee + billedMinutes * ratePerMinute).toFixed(2)} zł`;
        const distanceKm = Math.max(0.5, (elapsedSeconds / 60) * 0.18 + (vehicleId % 5) * 0.2);
        liveDistance.textContent = `${distanceKm.toFixed(2)} km`;
    };
    updateRideStats();
    window.setInterval(() => {
        elapsedSeconds += 1;
        updateRideStats();
    }, 1000);
});

const vehicleModal = document.querySelector("#vehicle-modal");
const vehicleModalContent = document.querySelector("#vehicle-modal-content");
if (vehicleModal && vehicleModalContent) {
    window.openVehicleModal = async (url) => {
        vehicleModal.showModal();
        vehicleModalContent.innerHTML = "<p class=\"muted\">Ładowanie szczegółów pojazdu...</p>";
        try {
            const response = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!response.ok) {
                throw new Error(`Nie udało się pobrać szczegółów pojazdu: HTTP ${response.status}`);
            }
            vehicleModalContent.innerHTML = await response.text();
            const modalMap = vehicleModalContent.querySelector(".vehicle-modal-map");
            if (modalMap) initializeLocationMap(modalMap);
        } catch (error) {
            console.error(error);
            vehicleModalContent.innerHTML = "<p class=\"message error\">Nie udało się wczytać szczegółów pojazdu. Spróbuj ponownie.</p>";
        }
    };

    document.addEventListener("click", (event) => {
        const modalButton = event.target.closest("[data-vehicle-modal]");
        if (modalButton) {
            window.openVehicleModal(modalButton.dataset.vehicleModal);
        } else if (event.target.closest("[data-modal-close]")) {
            vehicleModal.close();
        }
    });

    vehicleModal.addEventListener("click", (event) => {
        if (event.target === vehicleModal) vehicleModal.close();
    });
}

document.querySelectorAll("[data-reservation-expiry]").forEach((reservationExpiry) => {
    const expiresAt = new Date(reservationExpiry.dataset.reservationExpiry);
    window.setInterval(() => {
        const remainingSeconds = Math.max(0, Math.ceil((expiresAt.getTime() - Date.now()) / 1000));
        if (remainingSeconds === 0) {
            reservationExpiry.textContent = "Rezerwacja wygasła. Pojazd wraca do dostępnych.";
            window.setTimeout(() => window.location.reload(), 700);
            return;
        }
        const minutes = Math.floor(remainingSeconds / 60);
        const seconds = remainingSeconds % 60;
        reservationExpiry.textContent = `Rezerwacja wygasa za ${minutes}:${String(seconds).padStart(2, "0")}.`;
    }, 1000);
});
