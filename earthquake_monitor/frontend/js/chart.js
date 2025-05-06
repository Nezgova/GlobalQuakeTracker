/**
 * Charts component for earthquake visualization
 */
class EarthquakeCharts {
    constructor() {
        this.magnitudeChart = null;
        this.depthChart = null;
        this.timeChart = null;
        
        this.initCharts();
    }
    
    /**
     * Initialize chart containers
     */
    initCharts() {
        try {
            // Check if chart containers exist
            const magnitudeChartEl = document.getElementById('magnitude-chart');
            const depthChartEl = document.getElementById('depth-chart');
            const timeChartEl = document.getElementById('time-chart');
            
            if (!magnitudeChartEl || !depthChartEl || !timeChartEl) {
                console.warn('One or more chart containers not found');
            }
            
        } catch (error) {
            console.error('Error initializing charts:', error);
        }
    }
    
    /**
     * Update all charts with earthquake data
     * @param {Array} earthquakes - Array of earthquake features
     */
    updateCharts(earthquakes) {
        try {
            this.updateMagnitudeChart(earthquakes);
            this.updateDepthChart(earthquakes);
            this.updateTimeChart(earthquakes);
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }
    
    /**
     * Update magnitude distribution chart
     * @param {Array} earthquakes - Array of earthquake features
     */
    updateMagnitudeChart(earthquakes) {
        try {
            const chartElement = document.getElementById('magnitude-chart');
            if (!chartElement) {
                return;
            }
            
            // Destroy existing chart if it exists
            if (this.magnitudeChart) {
                this.magnitudeChart.destroy();
            }
            
            // Create magnitude bins
            const bins = {
                '0-1': 0,
                '1-2': 0,
                '2-3': 0,
                '3-4': 0,
                '4-5': 0,
                '5-6': 0,
                '6-7': 0,
                '7+': 0
            };
            
            // Count earthquakes in each bin
            earthquakes.forEach(eq => {
                const mag = eq.properties.mag;
                if (mag < 1) bins['0-1']++;
                else if (mag < 2) bins['1-2']++;
                else if (mag < 3) bins['2-3']++;
                else if (mag < 4) bins['3-4']++;
                else if (mag < 5) bins['4-5']++;
                else if (mag < 6) bins['5-6']++;
                else if (mag < 7) bins['6-7']++;
                else bins['7+']++;
            });
            
            // Create chart
            const ctx = chartElement.getContext('2d');
            this.magnitudeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(bins),
                    datasets: [{
                        label: 'Number of Earthquakes',
                        data: Object.values(bins),
                        backgroundColor: [
                            'rgba(163, 246, 0, 0.7)',   // 0-1
                            'rgba(220, 244, 0, 0.7)',   // 1-2
                            'rgba(247, 219, 17, 0.7)',  // 2-3
                            'rgba(253, 183, 42, 0.7)',  // 3-4
                            'rgba(252, 163, 93, 0.7)',  // 4-5
                            'rgba(255, 95, 101, 0.7)',  // 5-6
                            'rgba(255, 50, 50, 0.7)',   // 6-7
                            'rgba(190, 0, 0, 0.7)'      // 7+
                        ],
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
                                text: 'Number of Earthquakes'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Magnitude Range'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Earthquake Magnitude Distribution'
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Error updating magnitude chart:', error);
        }
    }
    
    /**
     * Update depth distribution chart
     * @param {Array} earthquakes - Array of earthquake features
     */
    updateDepthChart(earthquakes) {
        try {
            const chartElement = document.getElementById('depth-chart');
            if (!chartElement) {
                return;
            }
            
            // Destroy existing chart if it exists
            if (this.depthChart) {
                this.depthChart.destroy();
            }
            
            // Create depth bins (in km)
            const bins = {
                '0-10': 0,
                '10-30': 0,
                '30-70': 0,
                '70-150': 0,
                '150-300': 0,
                '300+': 0
            };
            
            // Count earthquakes in each bin
            earthquakes.forEach(eq => {
                const depth = eq.geometry.coordinates[2];
                if (depth < 10) bins['0-10']++;
                else if (depth < 30) bins['10-30']++;
                else if (depth < 70) bins['30-70']++;
                else if (depth < 150) bins['70-150']++;
                else if (depth < 300) bins['150-300']++;
                else bins['300+']++;
            });
            
            // Create chart
            const ctx = chartElement.getContext('2d');
            this.depthChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(bins),
                    datasets: [{
                        label: 'Number of Earthquakes',
                        data: Object.values(bins),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(255, 159, 64, 0.7)',
                            'rgba(255, 205, 86, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(153, 102, 255, 0.7)'
                        ],
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
                                text: 'Number of Earthquakes'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Depth Range (km)'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Earthquake Depth Distribution'
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Error updating depth chart:', error);
        }
    }
    
    /**
     * Update time distribution chart
     * @param {Array} earthquakes - Array of earthquake features
     */
    updateTimeChart(earthquakes) {
        try {
            const chartElement = document.getElementById('time-chart');
            if (!chartElement) {
                return;
            }
            
            // Destroy existing chart if it exists
            if (this.timeChart) {
                this.timeChart.destroy();
            }
            
            // Sort earthquakes by time (oldest first)
            const sortedEarthquakes = [...earthquakes].sort((a, b) => {
                return a.properties.time - b.properties.time;
            });
            
            // Prepare data for time chart
            const times = [];
            const magnitudes = [];
            const colors = [];
            
            sortedEarthquakes.forEach(eq => {
                const time = new Date(eq.properties.time);
                const mag = eq.properties.mag;
                
                times.push(time);
                magnitudes.push(mag);
                colors.push(this.getMagnitudeColor(mag));
            });
            
            // Create chart
            const ctx = chartElement.getContext('2d');
            this.timeChart = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Earthquakes',
                        data: times.map((time, i) => ({
                            x: time,
                            y: magnitudes[i]
                        })),
                        backgroundColor: colors,
                        borderColor: 'rgba(0, 0, 0, 0.3)',
                        borderWidth: 1,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'day',
                                displayFormats: {
                                    day: 'MMM D'
                                }
                            },
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Magnitude'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Earthquake Magnitudes Over Time'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const point = context.raw;
                                    return `Magnitude: ${point.y.toFixed(1)} - ${new Date(point.x).toLocaleString()}`;
                                }
                            }
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Error updating time chart:', error);
        }
    }
    
    /**
     * Get color based on earthquake magnitude
     * @param {number} magnitude - Earthquake magnitude
     * @returns {string} Color in rgba format
     */
    getMagnitudeColor(magnitude) {
        if (magnitude < 2) return 'rgba(163, 246, 0, 0.7)';   // Green
        if (magnitude < 3) return 'rgba(220, 244, 0, 0.7)';   // Yellow-green
        if (magnitude < 4) return 'rgba(247, 219, 17, 0.7)';  // Yellow
        if (magnitude < 5) return 'rgba(253, 183, 42, 0.7)';  // Orange
        if (magnitude < 6) return 'rgba(252, 163, 93, 0.7)';  // Light orange
        if (magnitude < 7) return 'rgba(255, 95, 101, 0.7)';  // Red-orange
        return 'rgba(190, 0, 0, 0.7)';                        // Dark red for 7+
    }
    
    /**
     * Update hazard analysis charts
     * @param {Object} analysisData - Analysis data
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
    }