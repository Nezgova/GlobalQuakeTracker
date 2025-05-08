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

        this.predictionSettings = {
            timeHorizon: 30,  // Default 30 days
            intensityThreshold: 4.0  // Default magnitude 4.0
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

        // Chart objects for later reference
        this.hazardCurveChart = null;
        this.probabilityTimeChart = null;
        this.riskComparisonChart = null;

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
        this.predictButton = document.getElementById('predict-button');
this.predictionStatusEl = document.getElementById('prediction-status');
this.predictionProbabilityEl = document.getElementById('prediction-probability');
this.predictionLikelihoodEl = document.getElementById('prediction-likelihood');
this.predictionTimeframeEl = document.getElementById('prediction-timeframe');
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

        document.getElementById('prediction-time-horizon').addEventListener('input', (e) => {
            this.predictionSettings.timeHorizon = e.target.value;
            document.getElementById('prediction-time-horizon-value').textContent = e.target.value;
        });
        
        document.getElementById('prediction-intensity-threshold').addEventListener('input', (e) => {
            this.predictionSettings.intensityThreshold = parseFloat(e.target.value);
            document.getElementById('prediction-intensity-threshold-value').textContent = e.target.value;
        });
        
        this.predictButton.addEventListener('click', () => this.performPrediction());
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
     * Perform hazard analysis using the API
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
            
            // Update charts with the analysis data
            this.updateHazardAnalysisCharts(analysisData);
            
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
     * Update hazard analysis UI with results
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
     * Set loading state for hazard analysis
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
     * Use current location for hazard analysis
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

    /**
     * Update visibility of advanced analysis options based on analysis type
     */
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

    /**
     * Update hazard analysis charts with new data
     * @param {Object} analysisData - Analysis results from API
     */
    updateHazardAnalysisCharts(analysisData) {
        // Only proceed if we have valid data
        if (!analysisData) {
            console.error('Cannot update hazard charts: missing data');
            return;
        }
        
        try {
            // Create basic chart data if not provided by backend
            if (!analysisData.hazard_curve && analysisData.probability !== undefined) {
                // Generate simple hazard curve data based on probability
                analysisData.hazard_curve = {
                    levels: [0.1, 0.2, 0.3, 0.4, 0.5],
                    poes: [
                        analysisData.probability,
                        analysisData.probability * 0.75,
                        analysisData.probability * 0.5,
                        analysisData.probability * 0.25,
                        analysisData.probability * 0.1
                    ]
                };
            }
            
            if (!analysisData.time_probabilities && analysisData.probability !== undefined) {
                // Generate simple time probability data
                analysisData.time_probabilities = {
                    "1": analysisData.probability,
                    "5": 1 - Math.pow(1 - analysisData.probability, 5),
                    "10": 1 - Math.pow(1 - analysisData.probability, 10),
                    "50": 1 - Math.pow(1 - analysisData.probability, 50)
                };
            }
            
            if (!analysisData.regional_comparison && analysisData.risk_level) {
                // Generate simple regional comparison
                const riskScore = {
                    'Low': 0.2,
                    'Moderate': 0.5,
                    'High': 0.7,
                    'Very High': 0.9
                }[analysisData.risk_level] || 0.3;
                
                analysisData.regional_comparison = {
                    'Selected Location': riskScore,
                    'Global Average': 0.3,
                    'Regional Average': 0.4,
                    'High Risk Zone': 0.8
                };
            }
            
            // Update hazard curve if data is available
            if (analysisData.hazard_curve) {
                this.displayHazardCurve(analysisData.hazard_curve);
            }
            
            // Update time probability chart
            if (analysisData.time_probabilities) {
                this.displayProbabilityByTimeChart(analysisData.time_probabilities);
            }
            
            // Update regional comparison chart
            if (analysisData.regional_comparison) {
                this.displayRiskComparisonChart(analysisData.regional_comparison);
            }
            
            // For advanced analysis type
            if (this.analysisSettings.type === 'advanced' && analysisData.openquake_results) {
                this.displayAdvancedAnalysisResults(analysisData);
            }
            
        } catch (error) {
            console.error('Error updating hazard analysis charts:', error);
        }
    }

    /**
     * Display hazard curve chart
     * @param {Object} hazardData - Hazard curve data with levels and poes arrays
     */
    displayHazardCurve(hazardData) {
        try {
            const chartElement = document.getElementById('hazard-curve-chart');
            if (!chartElement) {
                console.error('Hazard curve chart element not found');
                return;
            }
            
            // Destroy existing chart if it exists
            if (this.hazardCurveChart) {
                this.hazardCurveChart.destroy();
            }
            
            const ctx = chartElement.getContext('2d');
            
            // Create new chart with the data
            this.hazardCurveChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: hazardData.levels.map(level => level.toFixed(2) + 'g'),
                    datasets: [{
                        label: 'Probability of Exceedance',
                        data: hazardData.poes,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        pointRadius: 4,
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Seismic Hazard Curve'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Probability: ${(context.raw * 100).toFixed(2)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Peak Ground Acceleration (g)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Probability of Exceedance'
                            },
                            min: 0,
                            max: 1,
                            ticks: {
                                callback: function(value) {
                                    return (value * 100) + '%';
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error displaying hazard curve:', error);
        }
    }

    /**
     * Display probability by time chart
     * @param {Object} analysisData - Analysis data containing time probabilities
     */
    displayProbabilityByTimeChart(analysisData) {
        try {
            const chartElement = document.getElementById('probability-time-chart');
            if (!chartElement) {
                console.error('Probability time chart element not found');
                return;
            }
            
            // Destroy existing chart if it exists
            if (this.probabilityTimeChart) {
                this.probabilityTimeChart.destroy();
            }
            
            const ctx = chartElement.getContext('2d');
            const timeData = analysisData.time_probabilities;
            
            // Extract time periods and probabilities
            const timePeriods = Object.keys(timeData);
            const probabilities = timePeriods.map(period => timeData[period]);
            
            // Create chart
            this.probabilityTimeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: timePeriods.map(period => `${period} years`),
                    datasets: [{
                        label: 'Probability',
                        data: probabilities,
                        backgroundColor: probabilities.map(p => {
                            if (p < 0.1) return 'rgba(40, 167, 69, 0.7)';
                            if (p < 0.3) return 'rgba(255, 193, 7, 0.7)';
                            if (p < 0.6) return 'rgba(255, 87, 34, 0.7)';
                            return 'rgba(220, 53, 69, 0.7)';
                        }),
                        borderColor: 'rgba(0, 0, 0, 0.3)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Probability'
                            },
                            max: 1,
                            ticks: {
                                callback: function(value) {
                                    return (value * 100) + '%';
                                }
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time Period'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Earthquake Probability by Time Period'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Probability: ${(context.raw * 100).toFixed(2)}%`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error displaying probability by time chart:', error);
        }
    }

    /**
     * Display risk comparison chart
     * @param {Object} analysisData - Analysis data containing regional comparison
     */
    displayRiskComparisonChart(analysisData) {
        try {
            const chartElement = document.getElementById('risk-comparison-chart');
            if (!chartElement) {
                console.error('Risk comparison chart element not found');
                return;
            }
            
            // Destroy existing chart if it exists
            if (this.riskComparisonChart) {
                this.riskComparisonChart.destroy();
            }
            
            const ctx = chartElement.getContext('2d');
            const comparisonData = analysisData.regional_comparison;
            
            // Extract regions and their risk levels
            const regions = Object.keys(comparisonData);
            const riskScores = regions.map(region => comparisonData[region]);
            
            // Create chart
            this.riskComparisonChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: regions,
                    datasets: [{
                        label: 'Risk Score',
                        data: riskScores,
                        backgroundColor: regions.map((_, index) => {
                            const score = riskScores[index];
                            if (index === 0) return 'rgba(0, 123, 255, 0.8)'; // Highlight selected location
                            if (score < 0.3) return 'rgba(40, 167, 69, 0.6)';
                            if (score < 0.6) return 'rgba(255, 193, 7, 0.6)';
                            return 'rgba(220, 53, 69, 0.6)';
                        }),
                        borderColor: 'rgba(0, 0, 0, 0.3)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    scales: {
                        x: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Risk Score'
                            },
                            max: 1
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Regional Risk Comparison'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const score = context.raw;
                                    let riskText = 'Low Risk';
                                    if (score >= 0.7) riskText = 'Very High Risk';
                                    else if (score >= 0.5) riskText = 'High Risk';
                                    else if (score >= 0.3) riskText = 'Moderate Risk';
                                    return `${riskText} (Score: ${score.toFixed(2)})`;
                                }
                            }
                        },
                        legend: {
                            display: false
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error displaying risk comparison chart:', error);
        }
    }

    /**
     * Display advanced analysis results
     * @param {Object} advancedData - Advanced analysis data
     */
    displayAdvancedAnalysisResults(advancedData) {
        // Display any advanced analysis visualizations
        if (advancedData) {
            console.log("Processing advanced analysis data:", advancedData);
            
            // For OpenQuake results specifically
            if (advancedData.openquake_results) {
                console.log("OpenQuake results available:", advancedData.openquake_results);
                
                // Additional visualizations for OpenQuake results can be implemented here
                // For example, displaying hazard disaggregation or spectral acceleration
                if (advancedData.openquake_results.disaggregation) {
                    // Implement disaggregation visualization
                }
                
                if (advancedData.openquake_results.spectral_acceleration) {
                    // Implement spectral acceleration curve
                }
            }
            
            // Handle any other advanced analysis visualizations
            if (advancedData.vulnerability_assessment) {
                this.displayVulnerabilityAssessment(advancedData.vulnerability_assessment);
            }
        }
    }
    
    /**
     * Display vulnerability assessment visualization
     * @param {Object} vulnerabilityData - Vulnerability assessment data
     */
    displayVulnerabilityAssessment(vulnerabilityData) {
        // Implementation for vulnerability assessment visualization
        // This could include building fragility curves, damage probability matrices, etc.
        console.log("Displaying vulnerability assessment data:", vulnerabilityData);
        
        // Implementation would depend on the specific data structure and requirements
    }
    
    /**
     * Export current analysis data to CSV
     */
    exportAnalysisToCSV() {
        if (!this.hazardAnalysis.data) {
            alert('No analysis data available to export.');
            return;
        }
        
        try {
            // Prepare CSV data
            let csvContent = 'data:text/csv;charset=utf-8,';
            
            // Add headers
            csvContent += 'Parameter,Value\r\n';
            
            // Add coordinates
            csvContent += `Latitude,${this.latitudeInput.value}\r\n`;
            csvContent += `Longitude,${this.longitudeInput.value}\r\n`;
            csvContent += `Radius (km),${this.radiusInput.value}\r\n`;
            
            // Add analysis results
            const data = this.hazardAnalysis.data;
            
            if (data.probability !== undefined) {
                csvContent += `Probability,${data.probability}\r\n`;
            }
            
            if (data.risk_level) {
                csvContent += `Risk Level,${data.risk_level}\r\n`;
            }
            
            // Add time probabilities if available
            if (data.time_probabilities) {
                Object.entries(data.time_probabilities).forEach(([period, prob]) => {
                    csvContent += `Probability (${period} years),${prob}\r\n`;
                });
            }
            
            // Create download link
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', `earthquake_hazard_analysis_${new Date().toISOString().split('T')[0]}.csv`);
            document.body.appendChild(link);
            
            // Trigger download
            link.click();
            
            // Clean up
            document.body.removeChild(link);
            
        } catch (error) {
            console.error('Error exporting analysis to CSV:', error);
            alert('Failed to export analysis data.');
        }
    }

/**
 * Perform earthquake prediction analysis
 */
async performPrediction() {
    try {
        // Get values from inputs
        const latitude = parseFloat(this.latitudeInput.value);
        const longitude = parseFloat(this.longitudeInput.value);
        const timeHorizon = parseInt(this.predictionSettings.timeHorizon);
        const intensityThreshold = parseFloat(this.predictionSettings.intensityThreshold);
        
        // Validate inputs
        if (isNaN(latitude) || isNaN(longitude)) {
            throw new Error('Please enter valid numbers for latitude and longitude.');
        }
        
        if (latitude < -90 || latitude > 90) {
            throw new Error('Latitude must be between -90 and 90 degrees.');
        }
        
        if (longitude < -180 || longitude > 180) {
            throw new Error('Longitude must be between -180 and 180 degrees.');
        }
        
        // Set loading state
        this.setPredictionLoading(true);
        this.predictionStatusEl.textContent = 'Generating prediction...';
        this.predictionStatusEl.className = 'text-info';
        
        // Call the prediction API
        const response = await fetch(`${this.apiBaseUrl}/api/predict-earthquake`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                latitude: latitude,
                longitude: longitude,
                timeHorizon: timeHorizon,
                intensityThreshold: intensityThreshold
            })
        });
        
        if (!response.ok) {
            let errorData;
try {
    errorData = await response.json(); // Try to parse as JSON first
} catch (e) {
    errorData = await response.text(); // Fall back to text if not JSON
}
console.error('Server response error:', response.status, errorData);
throw new Error(`Server error: ${response.status}. ${JSON.stringify(errorData)}`);
        }
        
        // Process the prediction results
        let predictionData;
        try {
            predictionData = await response.json();
            if (typeof predictionData === 'string') {
                predictionData = JSON.parse(predictionData);
            }
        } catch (e) {
            console.error('Failed to parse prediction response:', e);
            throw new Error('Invalid JSON response from server');
        }
        console.log("Prediction response data:", predictionData);
        
        // Validate response data
        if (!predictionData || typeof predictionData !== 'object') {
            throw new Error('Invalid response data received from server');
        }
        
        // Store data and update UI
        this.predictionResults = predictionData;
        this.predictionError = null;
        this.updatePredictionUI();
        
        // Update charts with the prediction data
        this.updatePredictionCharts(predictionData);
        
        // Show the prediction area on the map if applicable
        if (this.map && this.map.showPredictionArea && predictionData.prediction_zone) {
            this.map.showPredictionArea(
                latitude, 
                longitude, 
                predictionData.prediction_zone.radius || 100,
                predictionData.prediction_probability
            );
        }
        
    } catch (error) {
        console.error('Error performing earthquake prediction:', error);
        this.predictionError = error.message || 'Failed to generate prediction';
        this.predictionResults = null;
        this.updatePredictionUI();
    } finally {
        this.setPredictionLoading(false);
    }
}

/**
 * Update prediction UI with results
 */
updatePredictionUI() {
    if (this.predictionError) {
        // Show error state
        this.predictionStatusEl.textContent = this.predictionError;
        this.predictionStatusEl.className = 'text-danger';
        
        // Clear previous results
        this.predictionProbabilityEl.textContent = 'N/A';
        this.predictionLikelihoodEl.textContent = 'N/A';
        this.predictionLikelihoodEl.className = '';
        this.predictionTimeframeEl.textContent = 'N/A';
        
    } else if (this.predictionResults) {
        // Show success state with data details
        const data = this.predictionResults;
        
        this.predictionStatusEl.textContent = 'Prediction complete';
        this.predictionStatusEl.className = 'text-success';
        
        // Update probability - safely handle missing data
        if (data.prediction_probability !== undefined) {
            const probability = data.prediction_probability * 100;
            this.predictionProbabilityEl.textContent = `${probability.toFixed(2)}%`;
        } else {
            this.predictionProbabilityEl.textContent = 'N/A';
        }
        
        // Update likelihood level with color coding
        const likelihood = data.likelihood_level;
        
        if (likelihood && typeof likelihood === 'string') {
            this.predictionLikelihoodEl.textContent = likelihood;
            
            // Add color class based on likelihood level
            this.predictionLikelihoodEl.className = '';
            switch (likelihood.toLowerCase()) {
                case 'very low':
                    this.predictionLikelihoodEl.className = 'text-success';
                    break;
                case 'low':
                    this.predictionLikelihoodEl.className = 'text-info';
                    break;
                case 'moderate':
                    this.predictionLikelihoodEl.className = 'text-warning';
                    break;
                case 'high':
                    this.predictionLikelihoodEl.className = 'text-danger';
                    break;
                case 'very high':
                    this.predictionLikelihoodEl.className = 'text-danger font-weight-bold';
                    break;
                default:
                    this.predictionLikelihoodEl.className = 'text-secondary';
                    break;
            }
        } else {
            this.predictionLikelihoodEl.textContent = 'Unknown';
            this.predictionLikelihoodEl.className = 'text-secondary';
        }
        
        // Update timeframe
        if (data.prediction_timeframe) {
            this.predictionTimeframeEl.textContent = data.prediction_timeframe;
        } else if (data.time_horizon) {
            this.predictionTimeframeEl.textContent = `Next ${data.time_horizon} days`;
        } else {
            this.predictionTimeframeEl.textContent = `Next ${this.predictionSettings.timeHorizon} days`;
        }
        
        // Show confidence interval if available
        if (data.confidence_interval) {
            document.getElementById('prediction-confidence').textContent = 
                `${data.confidence_interval.lower * 100}% - ${data.confidence_interval.upper * 100}%`;
            document.getElementById('prediction-confidence-container').classList.remove('d-none');
        } else {
            document.getElementById('prediction-confidence-container').classList.add('d-none');
        }
        
        // Show expected magnitude if available
        if (data.expected_magnitude) {
            document.getElementById('prediction-magnitude').textContent = 
                data.expected_magnitude.toFixed(1);
            document.getElementById('prediction-magnitude-container').classList.remove('d-none');
        } else {
            document.getElementById('prediction-magnitude-container').classList.add('d-none');
        }
    }
}

/**
 * Set loading state for prediction
 * @param {boolean} isLoading - Whether prediction is loading
 */
setPredictionLoading(isLoading) {
    if (isLoading) {
        this.predictButton.disabled = true;
        this.predictButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Predicting...';
    } else {
        this.predictButton.disabled = false;
        this.predictButton.textContent = 'Generate Prediction';
    }
}

/**
 * Update prediction charts with new data
 * @param {Object} predictionData - Prediction results from API
 */
updatePredictionCharts(predictionData) {
    // Only proceed if we have valid data
    if (!predictionData) {
        console.error('Cannot update prediction charts: missing data');
        return;
    }
    
    try {
        // Update probability timeline chart if data available
        if (predictionData.probability_timeline) {
            this.displayProbabilityTimelineChart(predictionData.probability_timeline);
        } else if (predictionData.prediction_probability) {
            // Generate simple timeline based on single probability value
            const timeHorizon = predictionData.time_horizon || this.predictionSettings.timeHorizon;
            const timeline = {};
            
            // Create an artificial timeline that grows towards the predicted probability
            for (let i = 1; i <= timeHorizon; i++) {
                // Exponential growth towards the final probability
                const factor = Math.pow(i / timeHorizon, 1.5);
                timeline[i] = predictionData.prediction_probability * factor;
            }
            
            this.displayProbabilityTimelineChart({ days: timeline });
        }
        
        // Update historical patterns chart if available
        if (predictionData.historical_patterns) {
            this.displayHistoricalPatternsChart(predictionData.historical_patterns);
        }
        
        // Update factor contribution chart if available
        if (predictionData.contributing_factors) {
            this.displayFactorContributionChart(predictionData.contributing_factors);
        }
        
    } catch (error) {
        console.error('Error updating prediction charts:', error);
    }
}

/**
 * Display probability timeline chart
 * @param {Object} timelineData - Timeline data with days as keys and probabilities as values
 */
displayProbabilityTimelineChart(timelineData) {
    try {
        const chartElement = document.getElementById('prediction-timeline-chart');
        if (!chartElement) {
            console.error('Prediction timeline chart element not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (this.predictionTimelineChart) {
            this.predictionTimelineChart.destroy();
        }
        
        const ctx = chartElement.getContext('2d');
        
        // Extract days and probabilities
        let labels, data;
        
        if (timelineData.days) {
            // Format where timeline is an object with days as keys
            labels = Object.keys(timelineData.days);
            data = labels.map(day => timelineData.days[day]);
        } else {
            // Format where timeline is an array of objects with day and probability
            labels = timelineData.map(item => `Day ${item.day}`);
            data = timelineData.map(item => item.probability);
        }
        
        // Create gradient for fill
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(255, 99, 132, 0.8)');
        gradient.addColorStop(1, 'rgba(255, 99, 132, 0.1)');
        
        // Create new chart
        this.predictionTimelineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Earthquake Probability',
                    data: data,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: gradient,
                    pointRadius: 4,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Prediction Probability Timeline'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Probability: ${(context.raw * 100).toFixed(2)}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Days from Now'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Probability'
                        },
                        min: 0,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return (value * 100) + '%';
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error displaying probability timeline chart:', error);
    }
}

/**
 * Display historical patterns chart
 * @param {Object} historicalData - Historical earthquake patterns data
 */
displayHistoricalPatternsChart(historicalData) {
    try {
        const chartElement = document.getElementById('historical-patterns-chart');
        if (!chartElement) {
            console.error('Historical patterns chart element not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (this.historicalPatternsChart) {
            this.historicalPatternsChart.destroy();
        }
        
        const ctx = chartElement.getContext('2d');
        
        // Prepare data for chart based on structure
        let labels, counts, averageMagnitudes;
        
        if (Array.isArray(historicalData)) {
            // Array of objects with period and count
            labels = historicalData.map(item => item.period);
            counts = historicalData.map(item => item.count);
            averageMagnitudes = historicalData.map(item => item.avg_magnitude || 0);
        } else {
            // Object with periods as keys
            labels = Object.keys(historicalData);
            counts = labels.map(period => historicalData[period].count || 0);
            averageMagnitudes = labels.map(period => historicalData[period].avg_magnitude || 0);
        }
        
        // Create new chart
        this.historicalPatternsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Earthquake Count',
                        data: counts,
                        backgroundColor: 'rgba(54, 162, 235, 0.7)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Average Magnitude',
                        data: averageMagnitudes,
                        type: 'line',
                        backgroundColor: 'rgba(255, 99, 132, 0.3)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        pointRadius: 4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Historical Earthquake Patterns'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Earthquake Count'
                        },
                        min: 0
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Average Magnitude'
                        },
                        min: 0,
                        max: 10,
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error displaying historical patterns chart:', error);
    }
}

/**
 * Display factor contribution chart
 * @param {Object} factorsData - Contributing factors data
 */
displayFactorContributionChart(factorsData) {
    try {
        const chartElement = document.getElementById('factor-contribution-chart');
        if (!chartElement) {
            console.error('Factor contribution chart element not found');
            return;
        }
        
        // Destroy existing chart if it exists
        if (this.factorContributionChart) {
            this.factorContributionChart.destroy();
        }
        
        const ctx = chartElement.getContext('2d');
        
        // Prepare data for chart
        let labels, values;
        
        if (Array.isArray(factorsData)) {
            // Array of objects with factor and contribution
            labels = factorsData.map(item => item.factor);
            values = factorsData.map(item => item.contribution);
        } else {
            // Object with factors as keys
            labels = Object.keys(factorsData);
            values = labels.map(factor => factorsData[factor]);
        }
        
        // Create new chart
        this.factorContributionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 206, 86, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 159, 64, 0.7)'
                    ],
                    borderColor: 'rgba(255, 255, 255, 0.8)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Contributing Factors to Prediction'
                    },
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                const percentage = (value * 100).toFixed(1);
                                return `${context.label}: ${percentage}%`;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error displaying factor contribution chart:', error);
    }
}

}
   
    // Initialize the application when DOM is loaded
    document.addEventListener('DOMContentLoaded', () => {
        const app = new EarthquakeApp();
        
        // Make app available globally for debugging if needed
        window.EarthquakeMonitor = app;
    });