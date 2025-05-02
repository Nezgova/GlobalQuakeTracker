/**
 * Earthquake Map functionality
 */
class EarthquakeMap {
    constructor() {
        this.map = null;
        this.markers = L.featureGroup();  // Changed to featureGroup
        this.initMap();
    }

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

    getMagnitudeColor(magnitude) {
        if (magnitude < 1) return '#A3F600';
        if (magnitude < 2) return '#DCF400';
        if (magnitude < 3) return '#F7DB11';
        if (magnitude < 4) return '#FDB72A';
        if (magnitude < 5) return '#FCA35D';
        if (magnitude < 6) return '#FF7F41';
        if (magnitude < 7) return '#FF5000';
        return '#FF0000';
    }

    getMarkerSize(magnitude) {
        return Math.max(5, Math.pow(magnitude, 2) * 0.8);
    }

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

    updateMap(earthquakes) {
        this.markers.clearLayers(); // Clear existing markers

        earthquakes.forEach(earthquake => {
            const magnitude = earthquake.properties.mag;
            const coordinates = earthquake.geometry.coordinates;
            
            const marker = L.circleMarker(
                [coordinates[1], coordinates[0]], 
                {
                    radius: this.getMarkerSize(magnitude),
                    fillColor: this.getMagnitudeColor(magnitude),
                    color: '#000',
                    weight: 1,
                    opacity: 0.8,
                    fillOpacity: 0.6
                }
            );

            marker.bindPopup(this.createPopupContent(earthquake));
            this.markers.addLayer(marker); // Add marker to the group
        });

        // Zoom to fit the bounds of all markers
        if (earthquakes.length > 0) {
            const bounds = this.markers.getBounds();
            if (bounds.isValid()) {
                this.map.fitBounds(bounds);  // Adjust map view
            }
        }
    }
}
