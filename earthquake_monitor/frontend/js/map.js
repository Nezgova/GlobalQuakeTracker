/**
 * Earthquake Map functionality
 */
class EarthquakeMap {
    constructor() {
        this.map = null;
        this.markers = L.layerGroup();
        this.initMap();
    }

    /**
     * Initialize Leaflet map
     */
    initMap() {
        // Create map with world view
        this.map = L.map('earthquake-map').setView([20, 0], 2);

        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18
        }).addTo(this.map);

        // Add empty marker layer group
        this.markers.addTo(this.map);
    }

    /**
     * Get color based on earthquake magnitude
     * @param {number} magnitude - Earthquake magnitude
     * @returns {string} - Color in hex format
     */
    getMagnitudeColor(magnitude) {
        if (magnitude < 1) return '#A3F600'; // Green
        if (magnitude < 2) return '#DCF400'; // Green-Yellow
        if (magnitude < 3) return '#F7DB11'; // Yellow
        if (magnitude < 4) return '#FDB72A'; // Orange-Yellow
        if (magnitude < 5) return '#FCA35D'; // Orange
        if (magnitude < 6) return '#FF7F41'; // Orange-Red
        if (magnitude < 7) return '#FF5000'; // Red-Orange
        return '#FF0000';                    // Red
    }

    /**
     * Calculate marker size based on magnitude
     * @param {number} magnitude - Earthquake magnitude
     * @returns {number} - Size in pixels
     */
    getMarkerSize(magnitude) {
        return Math.max(5, Math.pow(magnitude, 2) * 0.8);
    }

    /**
     * Create a popup with earthquake details
     * @param {Object} earthquake - Earthquake data
     * @returns {string} - HTML content for popup
     */
    createPopupContent(earthquake) {
        const date = new Date(earthquake.properties.time).toLocaleString();
        return `
            <div class="earthquake-popup">
                <h3>M ${earthquake.properties.mag.toFixed(1)} - ${earthquake.properties.place}</h3>
                <p><strong>Time:</strong> ${date}</p>
                <p><strong>Depth:</strong> ${earthquake.geometry.coordinates[2].toFixed(1)} km</p>
                <p><strong>Status:</strong> ${earthquake.properties.status}</p>
                <p><a href="${earthquake.properties.url}" target="_blank">More details</a></p>
            </div>
        `;
    }

    /**
     * Update the map with earthquake data
     * @param {Array} earthquakes - Array of earthquake features
     */
    updateMap(earthquakes) {
        // Clear existing markers
        this.markers.clearLayers();

        // Add new markers
        earthquakes.forEach(earthquake => {
            const magnitude = earthquake.properties.mag;
            const coordinates = earthquake.geometry.coordinates;
            
            // Create circle marker
            const marker = L.circleMarker(
                [coordinates[1], coordinates[0]], // Leaflet uses [lat, lng] while GeoJSON uses [lng, lat, depth]
                {
                    radius: this.getMarkerSize(magnitude),
                    fillColor: this.getMagnitudeColor(magnitude),
                    color: '#000',
                    weight: 1,
                    opacity: 0.8,
                    fillOpacity: 0.6
                }
            );

            // Add popup
            marker.bindPopup(this.createPopupContent(earthquake));
            
            // Add to marker layer
            this.markers.addLayer(marker);
        });

        // If there are earthquakes, zoom to fit them
        if (earthquakes.length > 0) {
            const bounds = this.markers.getBounds();
            if (bounds.isValid()) {
                this.map.fitBounds(bounds);
            }
        }
    }
}