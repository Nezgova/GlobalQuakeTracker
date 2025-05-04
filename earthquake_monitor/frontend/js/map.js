/**
 * Map visualization functionality for Earthquake Monitor
 */
class EarthquakeMap {
    constructor() {
        this.map = null;
        this.markers = L.featureGroup();  // Changed to featureGroup
        this.hazardCircle = null;  // Circle showing the hazard analysis area
        this.clickMarker = null;   // Marker for clicked location
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
        
        // Add click handler to map for setting coordinates
        this.map.on('click', (e) => {
            // Create custom event with lat/lng data
            const mapClickEvent = new CustomEvent('map-clicked', {
                detail: {
                    latlng: e.latlng
                }
            });
            
            // Dispatch the event to be caught by the app
            document.dispatchEvent(mapClickEvent);
            
            // Show temporary marker at click location
            this.showClickMarker(e.latlng.lat, e.latlng.lng);
        });
    }

    /**
     * Get marker color based on earthquake magnitude
     * @param {number} magnitude - Earthquake magnitude
     * @returns {string} - Hex color code
     */
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

    /**
     * Calculate marker size based on earthquake magnitude
     * @param {number} magnitude - Earthquake magnitude
     * @returns {number} - Marker radius in pixels
     */
    getMarkerSize(magnitude) {
        return Math.max(5, Math.pow(magnitude, 2) * 0.8);
    }

    /**
     * Create popup HTML for earthquake marker
     * @param {Object} earthquake - Earthquake GeoJSON feature
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
     * Update map with earthquake data
     * @param {Array} earthquakes - Array of earthquake GeoJSON features
     */
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
    
    /**
     * Show temporary marker at clicked location
     * @param {number} latitude - Latitude of clicked point
     * @param {number} longitude - Longitude of clicked point
     */
    showClickMarker(latitude, longitude) {
        // Remove existing marker if any
        if (this.clickMarker) {
            this.map.removeLayer(this.clickMarker);
        }
        
        // Create new marker
        this.clickMarker = L.marker([latitude, longitude], {
            icon: L.divIcon({
                className: 'click-marker',
                html: '<div class="pulse-marker"></div>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            })
        }).addTo(this.map);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (this.clickMarker) {
                this.map.removeLayer(this.clickMarker);
                this.clickMarker = null;
            }
        }, 5000);
    }
    
    /**
     * Show hazard analysis area on map
     * @param {number} latitude - Center latitude 
     * @param {number} longitude - Center longitude
     * @param {number} radius - Radius in km
     * @param {string} riskLevel - Risk level ('low', 'moderate', 'high', 'very high')
     */
    showHazardAnalysisArea(latitude, longitude, radius, riskLevel) {
        // Convert radius from km to meters for Leaflet
        const radiusInMeters = radius * 1000;
        
        // Remove existing hazard circle if any
        if (this.hazardCircle) {
            this.map.removeLayer(this.hazardCircle);
        }
        
        // Determine color based on risk level - Adding defensive check for undefined risk level
        let color = '#007bff'; // Default blue
        
        // First ensure riskLevel exists and is a string to prevent toLowerCase errors
        const safeRiskLevel = (riskLevel && typeof riskLevel === 'string') ? riskLevel : '';
        
        // Then use the safe value
        if (safeRiskLevel === 'low') {
            color = '#28a745'; // Green
        } else if (safeRiskLevel === 'moderate') {
            color = '#ffc107'; // Yellow
        } else if (safeRiskLevel === 'high') {
            color = '#dc3545'; // Red
        } else if (safeRiskLevel === 'very high') {
            color = '#9c0000'; // Dark red
        }
        // Default blue is already set
        
        // Create new circle
        this.hazardCircle = L.circle([latitude, longitude], {
            radius: radiusInMeters,
            color: color,
            fillColor: color,
            fillOpacity: 0.2,
            weight: 2
        }).addTo(this.map);
        
        // Create popup content - Handle undefined risk level
        const riskLevelDisplay = riskLevel && typeof riskLevel === 'string' ? riskLevel : 'Unknown';
        let riskLevelClass = 'risk-unknown';
        
        // Only attempt to use toLowerCase and replace if riskLevel is a valid string
        if (riskLevel && typeof riskLevel === 'string') {
            try {
                riskLevelClass = `risk-${riskLevel.toLowerCase().replace(' ', '-')}`;
            } catch (error) {
                console.warn('Error formatting risk level class:', error);
                riskLevelClass = 'risk-unknown';
            }
        }
        
        const popupContent = `
            <div class="hazard-analysis-popup">
                <h4>Hazard Analysis Area</h4>
                <p><strong>Center:</strong> ${latitude.toFixed(4)}, ${longitude.toFixed(4)}</p>
                <p><strong>Radius:</strong> ${radius} km</p>
                <p><strong>Risk Level:</strong> <span class="risk-level ${riskLevelClass}">${riskLevelDisplay}</span></p>
            </div>
        `;
        
        // Add popup to circle
        this.hazardCircle.bindPopup(popupContent);
        
        // Center map on the hazard area
        this.map.fitBounds(this.hazardCircle.getBounds());
    }
    
    /**
     * Center map on specified coordinates
     * @param {number} latitude - Latitude to center on
     * @param {number} longitude - Longitude to center on
     * @param {number} zoom - Optional zoom level (default: 10)
     */
    centerOn(latitude, longitude, zoom = 10) {
        this.map.setView([latitude, longitude], zoom);
        
        // Show temporary marker at this location
        this.showClickMarker(latitude, longitude);
    }
}