// Configuration de la carte
const mapConfig = {
    defaultCenter: [31.7917, -7.0926], // Centre du Maroc
    defaultZoom: 6,
    tileLayer: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
};

// Initialisation de la carte
function initMap() {
    const map = L.map('fire-map').setView(mapConfig.defaultCenter, mapConfig.defaultZoom);
    
    L.tileLayer(mapConfig.tileLayer, {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Ajout d'un événement de clic sur la carte
    map.on('click', function(e) {
        console.log('Coordonnées sélectionnées:', e.latlng);
    });
    
    return map;
}

// Mise à jour des marqueurs d'incendie
function updateFireMarkers(fires) {
    // Suppression des marqueurs existants
    if (window.fireMarkers) {
        window.fireMarkers.forEach(marker => marker.remove());
    }
    window.fireMarkers = [];
    
    // Ajout des nouveaux marqueurs
    fires.forEach(fire => {
        const marker = L.circleMarker([fire.lat, fire.lon], {
            radius: fire.intensity * 2,
            fillColor: getFireColor(fire.intensity),
            color: '#fff',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        });
        
        marker.bindPopup(createFirePopup(fire));
        marker.addTo(window.map);
        window.fireMarkers.push(marker);
    });
}

// Création du contenu du popup
function createFirePopup(fire) {
    const time = new Date(fire.time).toLocaleString();
    return `
        <div class="fire-popup">
            <h3>Incendie Détecté</h3>
            <p>🕒 ${time}</p>
            <p>🔥 Intensité: ${fire.intensity.toFixed(2)}</p>
            <p>📍 Position: ${fire.lat.toFixed(4)}, ${fire.lon.toFixed(4)}</p>
        </div>
    `;
}

// Détermination de la couleur en fonction de l'intensité
function getFireColor(intensity) {
    if (intensity < 3) return '#ffeb3b'; // Jaune
    if (intensity < 6) return '#ff9800'; // Orange
    if (intensity < 8) return '#f44336'; // Rouge
    return '#b71c1c'; // Rouge foncé
}

// Mise à jour du centre de la carte
function updateMapCenter(lat, lon) {
    if (window.map) {
        window.map.setView([lat, lon], window.map.getZoom());
    }
}

// Initialisation de la carte au chargement
document.addEventListener('DOMContentLoaded', () => {
    window.map = initMap();
}); 