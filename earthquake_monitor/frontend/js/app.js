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
        
        // Hazard analysis state
        this.hazardAnalysis = {
            loading: false,
            data: null,
            error: null
        };
        
        // API base URL - change this to work in any environment
        this.apiBaseUrl = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
            ? `http://${window.location.hostname}:5000` 
            : '/api'; // Fall back to relative path if deployed together
        
        // Bind DOM elements
        this.bindElements();
        this.bindEventListeners();
        
        this.analysisSettings = {
            type: 'standard', // Default analysis type (can be 'standard', 'advanced', or 'summary')
            intensityMeasureType: 'PGA' // For advanced analysis (PGA or other measures)
        };

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
        
        // Hazard Analysis Elements
        this.latitudeInput = document.getElementById('latitude-input');
        this.longitudeInput = document.getElementById('longitude-input');
        this.radiusInput = document.getElementById('radius-input');
        this.analyzeButton = document.getElementById('analyze-button');
        this.hazardProbabilityEl = document.getElementById('hazard-probability');
        this.hazardRiskLevelEl = document.getElementById('hazard-risk-level');
        this.hazardStatusEl = document.getElementById('hazard-status');
        this.useCurrentLocationButton = document.getElementById('use-current-location');

        this.analysisTypeSelect = document.getElementById('analysis-type');
        this.intensityMeasureSelect = document.getElementById('intensity-measure-type');
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
        
        // Hazard Analysis Listeners
        this.analyzeButton.addEventListener('click', () => this.performHazardAnalysis());
        
        if (this.analysisTypeSelect) {
            this.analysisTypeSelect.addEventListener('change', () => {
                this.analysisSettings.type = this.analysisTypeSelect.value;
                // Show/hide advanced options based on analysis type
                this.updateAnalysisOptionsVisibility();
            });
        }
        
        if (this.intensityMeasureSelect) {
            this.intensityMeasureSelect.addEventListener('change', () => {
                this.analysisSettings.intensityMeasureType = this.intensityMeasureSelect.value;
            });
        }
        
        // Use current location
        if (this.useCurrentLocationButton) {
            this.useCurrentLocationButton.addEventListener('click', () => this.useCurrentLocation());
        }
        
        // Use map click for coordinates
        if (this.map) {
            // Listen for custom event from map component
            document.addEventListener('map-clicked', (event) => {
                if (event.detail && event.detail.latlng) {
                    this.latitudeInput.value = event.detail.latlng.lat.toFixed(6);
                    this.longitudeInput.value = event.detail.latlng.lng.toFixed(6);
                }
            });
        }
        if (this.analysisTypeSelect) {
    this.analysisTypeSelect.addEventListener('change', () => {
        this.analysisSettings.type = this.analysisTypeSelect.value;
        // Show/hide advanced options based on analysis type
        this.updateAnalysisOptionsVisibility();
    });
}
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
                    title: `Earthquake Report (${new Date().toLocaleDateString()})`,
                    analysisType: this.analysisSettings.type 
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

    /**
     * NEW METHOD: Perform hazard analysis using the API
     */
    async performHazardAnalysis() {
        try {
            // Get values from inputs
            const latitude = parseFloat(this.latitudeInput.value);
            const longitude = parseFloat(this.longitudeInput.value);
            const radius = parseFloat(this.radiusInput.value);
            
            // Validate inputs
            if (isNaN(latitude) || isNaN(longitude) || isNaN(radius)) {
                throw new Error('Please enter valid numbers for latitude, longitude, and radius.');
            }
            
            if (radius <= 0) {
                throw new Error('Radius must be greater than zero.');
            }
            
            if (latitude < -90 || latitude > 90) {
                throw new Error('Latitude must be between -90 and 90 degrees.');
            }
            
            if (longitude < -180 || longitude > 180) {
                throw new Error('Longitude must be between -180 and 180 degrees.');
            }
            
            // Set loading state
            this.setHazardAnalysisLoading(true);
            
            // Choose API endpoint based on analysis type
            let endpoint;
            let requestBody = {
                latitude: latitude,
                longitude: longitude,
                radius: radius
            };
            
            // Add console log to debug analysis settings
            console.log("Current analysis settings:", this.analysisSettings);
            
            if (this.analysisSettings.type === 'advanced') {
                endpoint = `${this.apiBaseUrl}/api/advanced-analysis`;
                requestBody.intensityMeasureType = this.analysisSettings.intensityMeasureType;
            } else if (this.analysisSettings.type === 'summary') {
                endpoint = `${this.apiBaseUrl}/api/hazard-summary`;
            } else {
                // Default to standard analysis
                endpoint = `${this.apiBaseUrl}/api/analysis`;
                requestBody.analysisType = 'standard';
            }
            
            console.log(`Calling endpoint: ${endpoint} with data:`, requestBody);
            
            // Call the analysis API
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server response error:', response.status, errorText);
                throw new Error(`Server error: ${response.status}. ${errorText}`);
            }
            
            // Process the analysis results
            const analysisData = await response.json();
            console.log("Analysis response data:", analysisData);
            
            // Validate response data
            if (!analysisData || typeof analysisData !== 'object') {
                throw new Error('Invalid response data received from server');
            }
            
            // Store data and update UI
            this.hazardAnalysis.data = analysisData;
            this.hazardAnalysis.error = null;
            this.updateHazardAnalysisUI();
            
            // Update charts if we have the chart component
            if (this.charts && this.charts.updateHazardAnalysisCharts) {
                this.charts.updateHazardAnalysisCharts(analysisData);
            }
            
            // Check if analysisData has a valid risk_level before passing to map
            const riskLevel = analysisData && analysisData.risk_level ? 
                analysisData.risk_level : 'Unknown';
                
            // Show the results on the map
            if (this.map && this.map.showHazardAnalysisArea) {
                this.map.showHazardAnalysisArea(latitude, longitude, radius, riskLevel);
            }
            
        } catch (error) {
            console.error('Error performing hazard analysis:', error);
            this.hazardAnalysis.error = error.message || 'Failed to perform hazard analysis';
            this.hazardAnalysis.data = null;
            this.updateHazardAnalysisUI();
        } finally {
            this.setHazardAnalysisLoading(false);
        }
    }

    /**
     * NEW METHOD: Update hazard analysis UI with results
     */
    updateHazardAnalysisUI() {
        if (this.hazardAnalysis.error) {
            // Show error state
            this.hazardStatusEl.textContent = this.hazardAnalysis.error;
            this.hazardStatusEl.className = 'text-danger';
            
            // Clear previous results
            this.hazardProbabilityEl.textContent = 'N/A';
            this.hazardRiskLevelEl.textContent = 'N/A';
            this.hazardRiskLevelEl.className = '';
            
        } else if (this.hazardAnalysis.data) {
            // Show success state with data details
            const data = this.hazardAnalysis.data;
            console.log("Updating UI with data:", data);
            
            this.hazardStatusEl.textContent = 'Analysis complete';
            this.hazardStatusEl.className = 'text-success';
            
            // Update probability - safely handle missing data
            if (data.probability !== undefined) {
                const probability = data.probability * 100;
                this.hazardProbabilityEl.textContent = `${probability.toFixed(2)}%`;
            } else if (data.annual_probability !== undefined) {
                // Try alternative property name
                const probability = data.annual_probability * 100;
                this.hazardProbabilityEl.textContent = `${probability.toFixed(2)}% (annual)`;
            } else {
                this.hazardProbabilityEl.textContent = 'N/A - No probability data';
                console.warn("Missing probability data in analysis results:", data);
            }
            
            // Update risk level with color coding - safely handle missing data
            const riskLevel = data.risk_level || data.riskLevel || data.risk;
            
            if (riskLevel && typeof riskLevel === 'string') {
                this.hazardRiskLevelEl.textContent = riskLevel;
    
                // Add color class based on risk level
                this.hazardRiskLevelEl.className = '';
                switch (riskLevel.toLowerCase()) {
                    case 'low':
                        this.hazardRiskLevelEl.className = 'text-success';
                        break;
                    case 'moderate':
                        this.hazardRiskLevelEl.className = 'text-warning';
                        break;
                    case 'high':
                        this.hazardRiskLevelEl.className = 'text-danger';
                        break;
                    case 'very high':
                        this.hazardRiskLevelEl.className = 'text-danger font-weight-bold';
                        break;
                    default:
                        this.hazardRiskLevelEl.className = 'text-secondary';
                        break;
                }
            } else {
                // Handle case where riskLevel is missing
                this.hazardRiskLevelEl.textContent = 'Unknown - Missing risk data';
                this.hazardRiskLevelEl.className = 'text-secondary';
                console.warn("Missing risk level data in analysis results:", data);
            }
            
            // Display additional debug information if available
            if (data.message) {
                console.log("Server message:", data.message);
            }
        }
    }
    

    /**
     * NEW METHOD: Set loading state for hazard analysis
     * @param {boolean} isLoading - Whether analysis is loading
     */
    setHazardAnalysisLoading(isLoading) {
        this.hazardAnalysis.loading = isLoading;
        
        if (isLoading) {
            this.analyzeButton.disabled = true;
            this.analyzeButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            this.hazardStatusEl.textContent = 'Performing analysis, please wait...';
            this.hazardStatusEl.className = 'text-info';
        } else {
            this.analyzeButton.disabled = false;
            this.analyzeButton.textContent = 'Analyze Hazard';
        }
    }

    /**
     * NEW METHOD: Use current location for hazard analysis
     */
    useCurrentLocation() {
        if (navigator.geolocation) {
            this.useCurrentLocationButton.disabled = true;
            this.useCurrentLocationButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Getting location...';
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    // Success callback
                    const { latitude, longitude } = position.coords;
                    this.latitudeInput.value = latitude.toFixed(6);
                    this.longitudeInput.value = longitude.toFixed(6);
                    
                    // Reset button
                    this.useCurrentLocationButton.disabled = false;
                    this.useCurrentLocationButton.textContent = 'Use My Location';
                    
                    // Center map on this location if map exists and has centerOn method
                    if (this.map && this.map.centerOn) {
                        this.map.centerOn(latitude, longitude);
                    }
                },
                (error) => {
                    // Error callback
                    console.error('Geolocation error:', error);
                    let errorMessage = 'Unable to get your location. ';
                    
                    switch (error.code) {
                        case error.PERMISSION_DENIED:
                            errorMessage += 'Location access was denied. Please check your browser permissions.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMessage += 'Location information is unavailable.';
                            break;
                        case error.TIMEOUT:
                            errorMessage += 'Location request timed out.';
                            break;
                        default:
                            errorMessage += 'An unknown error occurred.';
                    }
                    
                    alert(errorMessage);
                    
                    // Reset button
                    this.useCurrentLocationButton.disabled = false;
                    this.useCurrentLocationButton.textContent = 'Use My Location';
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        } else {
            alert('Geolocation is not supported by your browser.');
        }
    }

    updateAnalysisOptionsVisibility() {
        const advancedOptionsContainer = document.getElementById('advanced-analysis-options');
        
        if (advancedOptionsContainer) {
            if (this.analysisSettings.type === 'advanced') {
                advancedOptionsContainer.classList.remove('d-none');
            } else {
                advancedOptionsContainer.classList.add('d-none');
            }
        }
    }

    updateHazardAnalysisCharts(analysisData) {
        // Only proceed if we have valid data
        if (!analysisData) {
            console.error('Cannot update hazard charts: missing data');
            return;
        }
        
        // Update hazard curve if data is available
        if (analysisData.hazard_curve) {
            this.displayHazardCurve(analysisData.hazard_curve);
        }
        
        // Update time probability chart
        if (analysisData.time_probabilities) {
            this.displayProbabilityByTimeChart(analysisData);
        }
        
        // Update regional comparison chart
        if (analysisData.regional_comparison) {
            this.displayRiskComparisonChart(analysisData);
        }
    }
  
    displayAdvancedAnalysisResults(advancedData) {
      // Display any advanced analysis visualizations
      if (this.charts && advancedData) {
          // Pass the data to charts class for display
          if (advancedData.hazard_curve) {
              this.charts.displayHazardCurve(advancedData.hazard_curve);
          }
          
          // For OpenQuake results specifically
          if (advancedData.openquake_results) {
              // Additional charts can be implemented here
              console.log("OpenQuake results available:", advancedData.openquake_results);
          }
      }
  }
}



// Initialize the app once DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new EarthquakeApp();
});