/**
 * Map component for earthquake visualization
 */
class EarthquakeMap {
    constructor() {
        this.map = null;
        this.markers = [];
        this.heatmap = null;
        this.analysisCircle = null;
        
        this.initMap();
    }
    
    /**
     * Initialize the map
     */
    initMap() {
        try {
            // Check if the map container exists
            const mapContainer = document.getElementById('earthquake-map');
            if (!mapContainer) {
                console.error('Map container not found');
                return;
            }
            
            // Create Leaflet map
            this.map = L.map('earthquake-map').setView([20, 0], 2);
            
            // Add tile layer
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 18
            }).addTo(this.map);
            
            // Add event listener for map clicks
            this.map.on('click', (e) => {
                // Create custom event with lat/lng
                const event = new CustomEvent('map-clicked', {
                    detail: {
                        latlng: e.latlng
                    }
                });
                
                // Dispatch the event
                document.dispatchEvent(event);
            });
            
        } catch (error) {
            console.error('Error initializing map:', error);
        }
    }
    
    /**
     * Update map with earthquake data
     * @param {Array} earthquakes - Array of earthquake features
     */
    updateMap(earthquakes) {
        try {
            if (!this.map) {
                console.error('Map not initialized');
                return;
            }
            
            // Clear existing markers
            this.clearMarkers();
            
            // Add new markers
            earthquakes.forEach(earthquake => {
                const coords = earthquake.geometry.coordinates;
                const magnitude = earthquake.properties.mag;
                const location = earthquake.properties.place || 'Unknown location';
                const time = new Date(earthquake.properties.time).toLocaleString();
                const depth = coords[2].toFixed(1);
                
                // Create marker with size based on magnitude
                const markerSize = Math.max(5, magnitude * 2);
                const markerColor = this.getMagnitudeColor(magnitude);
                
                const marker = L.circleMarker([coords[1], coords[0]], {
                    radius: markerSize,
                    color: '#000',
                    weight: 1,
                    fillColor: markerColor,
                    fillOpacity: 0.8
                });
                
                // Add popup with earthquake info
                marker.bindPopup(`
                    <strong>Magnitude:</strong> ${magnitude}<br>
                    <strong>Location:</strong> ${location}<br>
                    <strong>Time:</strong> ${time}<br>
                    <strong>Depth:</strong> ${depth} km
                `);
                
                // Add marker to map and markers array
                marker.addTo(this.map);
                this.markers.push(marker);
            });
            
            // Create heatmap layer if we have enough earthquakes
            if (earthquakes.length > 10) {
                this.createHeatmap(earthquakes);
            }
            
            // Fit map to markers if we have any
            if (this.markers.length > 0) {
                const group = new L.featureGroup(this.markers);
                this.map.fitBounds(group.getBounds());
            }
            
        } catch (error) {
            console.error('Error updating map:', error);
        }
    }
    
    /**
     * Clear all markers and heatmap from map
     */
    clearMarkers() {
        // Remove markers
        this.markers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers = [];
        
        // Remove heatmap if it exists
        if (this.heatmap) {
            this.map.removeLayer(this.heatmap);
            this.heatmap = null;
        }
    }
    
    /**
     * Create heatmap from earthquake data
     * @param {Array} earthquakes - Array of earthquake features
     */
    createHeatmap(earthquakes) {
        try {
            // Check if heatmap plugin is available
            if (!L.heatLayer) {
                console.warn('Leaflet.heat plugin not available');
                return;
            }
            
            // Create points array for heatmap with intensity based on magnitude
            const points = earthquakes.map(eq => {
                const coords = eq.geometry.coordinates;
                const intensity = Math.pow(2, eq.properties.mag) / 2; // Exponential scaling for better visualization
                return [coords[1], coords[0], intensity];
            });
            
            // Create heatmap layer
            this.heatmap = L.heatLayer(points, {
                radius: 20,
                blur: 15,
                maxZoom: 10,
                gradient: {
                    0.2: '#ffffb2',
                    0.4: '#fecc5c',
                    0.6: '#fd8d3c',
                    0.8: '#f03b20',
                    1.0: '#bd0026'
                }
            }).addTo(this.map);
            
        } catch (error) {
            console.error('Error creating heatmap:', error);
        }
    }
    
    /**
     * Get color based on earthquake magnitude
     * @param {number} magnitude - Earthquake magnitude
     * @returns {string} Color in hex format
     */
    getMagnitudeColor(magnitude) {
        if (magnitude < 2) return '#A3F600'; // Green
        if (magnitude < 3) return '#DCF400'; // Yellow-green
        if (magnitude < 4) return '#F7DB11'; // Yellow
        if (magnitude < 5) return '#FDB72A'; // Orange
        if (magnitude < 6) return '#FCA35D'; // Light orange
        if (magnitude < 7) return '#FF5F65'; // Red-orange
        return '#FF0000'; // Red for 7+
    }
    
    /**
     * Center map on specified coordinates
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @param {number} zoom - Zoom level (optional)
     */
    centerOn(lat, lng, zoom = 10) {
        if (this.map) {
            this.map.setView([lat, lng], zoom);
        }
    }
    
    /**
     * Show hazard analysis area on the map
     * @param {number} lat - Latitude of center
     * @param {number} lng - Longitude of center
     * @param {number} radius - Radius in kilometers
     * @param {string} riskLevel - Risk level (Low, Moderate, High, Very High)
     */
    showHazardAnalysisArea(lat, lng, radius, riskLevel) {
        try {
            if (!this.map) {
                console.error('Map not initialized');
                return;
            }
            
            // Remove existing analysis circle if it exists
            if (this.analysisCircle) {
                this.map.removeLayer(this.analysisCircle);
            }
            
            // Convert radius from km to meters for Leaflet
            const radiusMeters = radius * 1000;
            
            // Get color based on risk level
            let color;
            switch (riskLevel.toLowerCase()) {
                case 'low':
                    color = '#28a745'; // Green
                    break;
                case 'moderate':
                    color = '#ffc107'; // Yellow
                    break;
                case 'high':
                    color = '#fd7e14'; // Orange
                    break;
                case 'very high':
                    color = '#dc3545'; // Red
                    break;
                default:
                    color = '#17a2b8'; // Blue (unknown)
                    break;
            }
            
            // Create circle
            this.analysisCircle = L.circle([lat, lng], {
                radius: radiusMeters,
                color: color,
                fillColor: color,
                fillOpacity: 0.2,
                weight: 2
            }).addTo(this.map);
            
            // Add marker at center
            const marker = L.marker([lat, lng]).addTo(this.map);
            this.markers.push(marker);
            
            // Bind popup with information
            marker.bindPopup(`
                <strong>Analysis Center</strong><br>
                Latitude: ${lat.toFixed(6)}<br>
                Longitude: ${lng.toFixed(6)}<br>
                Radius: ${radius} km<br>
                Risk Level: ${riskLevel}
            `);
            
            // Fit map to circle
            this.map.fitBounds(this.analysisCircle.getBounds());
            
        } catch (error) {
            console.error('Error showing hazard analysis area:', error);
        }
    }
}