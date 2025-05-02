/**
 * Main application logic for Earthquake Monitor
 */
class EarthquakeApp {
    constructor() {
        // Initialize components
        this.map = new EarthquakeMap();
        this.charts = new EarthquakeCharts();
        
        // Internal state
        this.earthquakes = [];
        this.filteredEarthquakes = [];
        this.filterSettings = {
            minMagnitude: 1.0,
            timePeriod: 'day'
        };
        
        // API base URL - change this to work in any environment
        this.apiBaseUrl = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
            ? `http://${window.location.hostname}:5000` 
            : '/api'; // Fall back to relative path if deployed together
        
        // Bind DOM elements
        this.bindElements();
        this.bindEventListeners();
        
        // Initial data load
        this.loadEarthquakeData();
    }

    /**
     * Get references to DOM elements
     */
    bindElements() {
        // Metric displays
        this.earthquakeCountEl = document.getElementById('earthquake-count');
        this.avgMagnitudeEl = document.getElementById('avg-magnitude');
        this.strongestMagnitudeEl = document.getElementById('strongest-magnitude');
        
        // Controls
        this.minMagnitudeSlider = document.getElementById('min-magnitude');
        this.minMagnitudeValue = document.getElementById('min-magnitude-value');
        this.timePeriodSelect = document.getElementById('time-period');
        this.refreshButton = document.getElementById('refresh-data');
        this.reportButton = document.getElementById('generate-report');
        
        // Earthquake list
        this.earthquakeListEl = document.getElementById('earthquake-list');
    }

    /**
     * Set up event listeners
     */
    bindEventListeners() {
        // Filter controls
        this.minMagnitudeSlider.addEventListener('input', () => {
            const value = parseFloat(this.minMagnitudeSlider.value);
            this.minMagnitudeValue.textContent = value.toFixed(1);
            this.filterSettings.minMagnitude = value;
            this.applyFilters();
        });
        
        this.timePeriodSelect.addEventListener('change', () => {
            this.filterSettings.timePeriod = this.timePeriodSelect.value;
            this.loadEarthquakeData();
        });
        
        // Buttons
        this.refreshButton.addEventListener('click', () => this.loadEarthquakeData());
        this.reportButton.addEventListener('click', () => this.generateReport());
    }

    /**
     * Load earthquake data from USGS API
     */
    async loadEarthquakeData() {
        try {
            this.setLoading(true);
            
            // Convert time period to days for backend API
            let days;
            switch (this.filterSettings.timePeriod) {
                case 'hour': days = 0.042; break; // ~1 hour in days
                case 'day': days = 1; break;
                case 'week': days = 7; break;
                case 'month': days = 30; break;
                default: days = 1;
            }
            
            // Try to fetch from our backend first
            try {
                const response = await fetch(`${this.apiBaseUrl}/api/earthquakes?days=${days}&magnitude=${this.filterSettings.minMagnitude}`);
                if (response.ok) {
                    const data = await response.json();
                    this.processEarthquakeData(data);
                    return;
                }
            } catch (error) {
                console.log('Backend not available, falling back to direct USGS API', error);
            }
            
            // Fall back to direct USGS API if backend is not available
            const period = this.filterSettings.timePeriod;
            const apiUrl = `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_${period}.geojson`;
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            this.processEarthquakeData(data);
            
        } catch (error) {
            console.error('Error loading earthquake data:', error);
            alert('Failed to load earthquake data. Please try again later.');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Process earthquake data from API
     * @param {Object} data - GeoJSON data from USGS API
     */
    processEarthquakeData(data) {
        // Store full earthquake data
        this.earthquakes = data.features;
        
        // Apply filters
        this.applyFilters();
    }

    /**
     * Apply filters to earthquake data
     */
    applyFilters() {
        // Filter earthquakes by minimum magnitude
        this.filteredEarthquakes = this.earthquakes.filter(earthquake => {
            return earthquake.properties.mag >= this.filterSettings.minMagnitude;
        });
        
        // Update UI with filtered data
        this.updateUI();
    }

    /**
     * Update all UI components with filtered earthquake data
     */
    updateUI() {
        // Update metrics
        this.updateMetrics();
        
        // Update map
        this.map.updateMap(this.filteredEarthquakes);
        
        // Update charts
        this.charts.updateCharts(this.filteredEarthquakes);
        
        // Update earthquake list
        this.updateEarthquakeList();
    }

    /**
     * Update metric displays
     */
    updateMetrics() {
        // Total earthquakes
        this.earthquakeCountEl.textContent = this.filteredEarthquakes.length;
        
        // Average magnitude
        if (this.filteredEarthquakes.length > 0) {
            const totalMagnitude = this.filteredEarthquakes.reduce((sum, eq) => {
                return sum + eq.properties.mag;
            }, 0);
            const avgMagnitude = totalMagnitude / this.filteredEarthquakes.length;
            this.avgMagnitudeEl.textContent = avgMagnitude.toFixed(2);
        } else {
            this.avgMagnitudeEl.textContent = 'N/A';
        }
        
        // Strongest earthquake
        if (this.filteredEarthquakes.length > 0) {
            const strongest = this.filteredEarthquakes.reduce((max, eq) => {
                return eq.properties.mag > max.properties.mag ? eq : max;
            }, this.filteredEarthquakes[0]);
            
            this.strongestMagnitudeEl.textContent = `${strongest.properties.mag.toFixed(1)} (${strongest.properties.place})`;
        } else {
            this.strongestMagnitudeEl.textContent = 'N/A';
        }
    }

    /**
     * Update earthquake list table
     */
    updateEarthquakeList() {
        // Clear existing list
        this.earthquakeListEl.innerHTML = '';
        
        if (this.filteredEarthquakes.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="4">No earthquakes match the current filters</td>';
            this.earthquakeListEl.appendChild(row);
            return;
        }
        
        // Sort earthquakes by time (newest first)
        const sortedEarthquakes = [...this.filteredEarthquakes].sort((a, b) => {
            return b.properties.time - a.properties.time;
        });
        
        // Add earthquakes to list (limit to 50 for performance)
        const limit = Math.min(sortedEarthquakes.length, 50);
        for (let i = 0; i < limit; i++) {
            const earthquake = sortedEarthquakes[i];
            const row = document.createElement('tr');
            
            // Format time
            const time = new Date(earthquake.properties.time).toLocaleString();
            
            // Format location
            const location = earthquake.properties.place || 'Unknown location';
            
            // Format depth
            const depth = earthquake.geometry.coordinates[2].toFixed(1) + ' km';
            
            // Add row data
            row.innerHTML = `
                <td>${time}</td>
                <td>${earthquake.properties.mag.toFixed(1)}</td>
                <td>${location}</td>
                <td>${depth}</td>
            `;
            
            this.earthquakeListEl.appendChild(row);
        }
    }

    /**
     * Generate and download PDF report
     */
    async generateReport() {
        try {
            // Check if we have earthquake data
            if (this.filteredEarthquakes.length === 0) {
                alert('No earthquake data available for report. Please adjust filters or refresh data.');
                return;
            }
            
            // Show loading state
            this.reportButton.disabled = true;
            this.reportButton.textContent = 'Generating...';
            
            // Get the strongest earthquake's coordinates for the report center
            // If no earthquakes match, use a default location
            let latitude, longitude;
            if (this.filteredEarthquakes.length > 0) {
                const strongest = this.filteredEarthquakes.reduce((max, eq) => {
                    return eq.properties.mag > max.properties.mag ? eq : max;
                }, this.filteredEarthquakes[0]);
                
                // Get coordinates from the strongest earthquake
                longitude = strongest.geometry.coordinates[0];
                latitude = strongest.geometry.coordinates[1];
            } else {
                // Default coordinates (San Francisco as an example)
                latitude = 37.7749;
                longitude = -122.4194;
            }
            
            // Convert time period to days for API consistency
            let days;
            switch (this.filterSettings.timePeriod) {
                case 'hour': days = 0.042; break; // ~1 hour in days
                case 'day': days = 1; break;
                case 'week': days = 7; break;
                case 'month': days = 30; break;
                default: days = 1;
            }
            
            // Call backend to generate report with required parameters
            const response = await fetch(`${this.apiBaseUrl}/api/report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    latitude: latitude,
                    longitude: longitude,
                    radius: 300, // Default 300km radius
                    days: days,
                    minMagnitude: this.filterSettings.minMagnitude,
                    earthquakeCount: this.filteredEarthquakes.length,
                    title: `Earthquake Report (${new Date().toLocaleDateString()})`
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Get the PDF blob
            const blob = await response.blob();
            
            // Create a URL for the blob
            const url = window.URL.createObjectURL(blob);
            
            // Create a link to download the PDF
            const a = document.createElement('a');
            a.href = url;
            a.download = `earthquake_report_${new Date().toISOString().split('T')[0]}.pdf`;
            a.click();
            
            // Clean up
            window.URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Error generating report:', error);
            alert('Failed to generate report. Please try again later.');
        } finally {
            // Reset button state
            this.reportButton.disabled = false;
            this.reportButton.textContent = 'Generate PDF Report';
        }
    }

    /**
     * Set loading state for the application
     * @param {boolean} isLoading - Whether the app is in loading state
     */
    setLoading(isLoading) {
        if (isLoading) {
            this.refreshButton.disabled = true;
            this.refreshButton.textContent = 'Loading...';
        } else {
            this.refreshButton.disabled = false;
            this.refreshButton.textContent = 'Refresh Data';
        }
    }
}

// Initialize the app once DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new EarthquakeApp();
});