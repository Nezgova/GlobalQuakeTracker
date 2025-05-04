/**
 * Chart visualization functionality for Earthquake Monitor
 */
class EarthquakeCharts {
  constructor() {
      this.magnitudeChart = null;
      this.hazardCurveChart = null;
      this.initCharts();
  }

  /**
   * Initialize Chart.js charts
   */
  initCharts() {
      // Initialize magnitude distribution chart
      const magnitudeCtx = document.getElementById('magnitude-chart').getContext('2d');
      
      // Create empty magnitude distribution chart
      this.magnitudeChart = new Chart(magnitudeCtx, {
          type: 'bar',
          data: {
              labels: ['0-1', '1-2', '2-3', '3-4', '4-5', '5-6', '6-7', '7+'],
              datasets: [{
                  label: 'Earthquakes by Magnitude',
                  data: [0, 0, 0, 0, 0, 0, 0, 0],
                  backgroundColor: [
                      '#A3F600', // Green
                      '#DCF400', // Green-Yellow
                      '#F7DB11', // Yellow
                      '#FDB72A', // Orange-Yellow
                      '#FCA35D', // Orange
                      '#FF7F41', // Orange-Red
                      '#FF5000', // Red-Orange
                      '#FF0000'  // Red
                  ],
                  borderColor: '#333',
                  borderWidth: 1
              }]
          },
          options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                  legend: {
                      display: false
                  },
                  title: {
                      display: true,
                      text: 'Earthquake Magnitude Distribution',
                      font: {
                          size: 16
                      }
                  }
              },
              scales: {
                  y: {
                      beginAtZero: true,
                      title: {
                          display: true,
                          text: 'Number of Earthquakes'
                      },
                      ticks: {
                          stepSize: 1
                      }
                  },
                  x: {
                      title: {
                          display: true,
                          text: 'Magnitude Range'
                      }
                  }
              }
          }
      });
      
      // Initialize empty hazard curve chart if the element exists
      const hazardCurveElement = document.getElementById('hazard-curve-chart');
      if (hazardCurveElement) {
          const hazardCtx = hazardCurveElement.getContext('2d');
          
          // Create empty hazard curve chart
          this.hazardCurveChart = new Chart(hazardCtx, {
              type: 'line',
              data: {
                  labels: [],
                  datasets: [{
                      label: 'Annual Probability of Exceedance',
                      data: [],
                      borderColor: 'rgba(255, 99, 132, 1)',
                      backgroundColor: 'rgba(255, 99, 132, 0.2)',
                      pointRadius: 3,
                      tension: 0.1
                  }]
              },
              options: {
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                      x: {
                          title: {
                              display: true,
                              text: 'Peak Ground Acceleration (g)'
                          },
                          type: 'logarithmic'
                      },
                      y: {
                          title: {
                              display: true,
                              text: 'Annual Probability of Exceedance'
                          },
                          type: 'logarithmic'
                      }
                  },
                  plugins: {
                      title: {
                          display: true,
                          text: 'Seismic Hazard Curve'
                      }
                  }
              }
          });
      }
  }

  /**
   * Count earthquakes by magnitude range
   * @param {Array} earthquakes - Array of earthquake features
   * @returns {Array} - Array of counts for each magnitude range
   */
  countByMagnitude(earthquakes) {
      const counts = [0, 0, 0, 0, 0, 0, 0, 0];
      
      earthquakes.forEach(earthquake => {
          const mag = earthquake.properties.mag;
          
          if (mag < 1) counts[0]++;
          else if (mag < 2) counts[1]++;
          else if (mag < 3) counts[2]++;
          else if (mag < 4) counts[3]++;
          else if (mag < 5) counts[4]++;
          else if (mag < 6) counts[5]++;
          else if (mag < 7) counts[6]++;
          else counts[7]++;
      });
      
      return counts;
  }

  /**
   * Update charts with earthquake data
   * @param {Array} earthquakes - Array of earthquake features
   */
  updateCharts(earthquakes) {
      // Update magnitude distribution chart
      const magnitudeCounts = this.countByMagnitude(earthquakes);
      
      this.magnitudeChart.data.datasets[0].data = magnitudeCounts;
      this.magnitudeChart.update();
  }

  /**
   * Display hazard curve chart with analysis data
   * @param {Object} hazardData - Hazard analysis data with levels and probabilities
   */
  displayHazardCurve(hazardData) {
      // Check if we have the chart element and data
      if (!this.hazardCurveChart || !hazardData || !hazardData.levels || !hazardData.poes) {
          console.error('Cannot display hazard curve: missing chart or data');
          return;
      }
      
      // Extract data from hazard curves
      const pgaLevels = hazardData.levels;
      const pgaProbabilities = hazardData.poes;
      
      // Update chart data
      this.hazardCurveChart.data.labels = pgaLevels.map(level => level.toFixed(3) + 'g');
      this.hazardCurveChart.data.datasets[0].data = pgaProbabilities;
      
      // Update chart
      this.hazardCurveChart.update();
  }
  
  /**
   * Display probability by time chart
   * @param {Object} analysisResults - Analysis results including probability data
   */
  displayProbabilityByTimeChart(analysisResults) {
      // Find the chart element
      const timeChartEl = document.getElementById('probability-time-chart');
      if (!timeChartEl || !analysisResults || !analysisResults.time_probabilities) {
          return;
      }
      
      // Destroy existing chart if it exists
      if (this.probabilityTimeChart) {
          this.probabilityTimeChart.destroy();
      }
      
      const ctx = timeChartEl.getContext('2d');
      const timeData = analysisResults.time_probabilities;
      
      // Extract time periods and probabilities
      const timePeriods = Object.keys(timeData);
      const probabilities = timePeriods.map(period => timeData[period] * 100); // Convert to percentage
      
      // Create chart
      this.probabilityTimeChart = new Chart(ctx, {
          type: 'bar',
          data: {
              labels: timePeriods.map(period => `${period} years`),
              datasets: [{
                  label: 'Probability (%)',
                  data: probabilities,
                  backgroundColor: probabilities.map(p => {
                      // Color based on probability
                      if (p < 10) return 'rgba(40, 167, 69, 0.7)'; // Green
                      if (p < 30) return 'rgba(255, 193, 7, 0.7)'; // Yellow
                      if (p < 60) return 'rgba(255, 87, 34, 0.7)'; // Orange
                      return 'rgba(220, 53, 69, 0.7)'; // Red
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
                          text: 'Probability (%)'
                      },
                      max: 100
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
                      text: 'Earthquake Probability by Time Period',
                      font: {
                          size: 16
                      }
                  },
                  tooltip: {
                      callbacks: {
                          label: function(context) {
                              return `Probability: ${context.raw.toFixed(2)}%`;
                          }
                      }
                  }
              }
          }
      });
  }
  
  /**
   * Display risk comparison chart
   * @param {Object} analysisResults - Analysis results including comparison data
   */
  displayRiskComparisonChart(analysisResults) {
      // Find the chart element
      const comparisonChartEl = document.getElementById('risk-comparison-chart');
      if (!comparisonChartEl || !analysisResults || !analysisResults.regional_comparison) {
          return;
      }
      
      // Destroy existing chart if it exists
      if (this.riskComparisonChart) {
          this.riskComparisonChart.destroy();
      }
      
      const ctx = comparisonChartEl.getContext('2d');
      const comparisonData = analysisResults.regional_comparison;
      
      // Extract regions and their risk levels
      const regions = Object.keys(comparisonData);
      const riskScores = regions.map(region => comparisonData[region]);
      
      // Find current location's index (assuming it's included in the comparison)
      const currentLocationIndex = regions.findIndex(r => r === 'Selected Location');
      
      // Create background colors array, highlighting current location
      const backgroundColors = riskScores.map((score, index) => {
          // Highlight the current location
          if (index === currentLocationIndex) {
              return 'rgba(0, 123, 255, 0.8)'; // Blue for current location
          }
          
          // Color others based on risk score
          if (score < 0.3) return 'rgba(40, 167, 69, 0.6)'; // Green
          if (score < 0.6) return 'rgba(255, 193, 7, 0.6)'; // Yellow
          return 'rgba(220, 53, 69, 0.6)'; // Red
      });
      
      // Create chart
      this.riskComparisonChart = new Chart(ctx, {
          type: 'bar',
          data: {
              labels: regions,
              datasets: [{
                  label: 'Risk Level',
                  data: riskScores,
                  backgroundColor: backgroundColors,
                  borderColor: 'rgba(0, 0, 0, 0.3)',
                  borderWidth: 1
              }]
          },
          options: {
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y', // Horizontal bar chart
              scales: {
                  x: {
                      beginAtZero: true,
                      title: {
                          display: true,
                          text: 'Relative Risk Score'
                      },
                      max: 1.0
                  }
              },
              plugins: {
                  title: {
                      display: true,
                      text: 'Regional Risk Comparison',
                      font: {
                          size: 16
                      }
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
                  }
              }
          }
      });
  }
  
  /**
   * Update all hazard analysis charts based on new analysis data
   * @param {Object} analysisData - Complete analysis data from the API
   */


displayHazardSpectrum(spectrumData) {
    // Find the chart element
    const spectrumChartEl = document.getElementById('hazard-spectrum-chart');
    if (!spectrumChartEl || !spectrumData || !spectrumData.periods || !spectrumData.accelerations) {
        return;
    }
    
    // Destroy existing chart if it exists
    if (this.hazardSpectrumChart) {
        this.hazardSpectrumChart.destroy();
    }
    
    const ctx = spectrumChartEl.getContext('2d');
    
    // Create chart
    this.hazardSpectrumChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: spectrumData.periods,
            datasets: [{
                label: 'Spectral Acceleration (g)',
                data: spectrumData.accelerations,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                pointRadius: 3,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Period (s)'
                    },
                    type: 'logarithmic'
                },
                y: {
                    title: {
                        display: true,
                        text: 'Spectral Acceleration (g)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Response Spectrum'
                }
            }
        }
    });
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
    
    // Display OpenQuake-specific results
    if (analysisData.advanced_analysis && analysisData.advanced_analysis.hazard_spectrum) {
        this.displayHazardSpectrum(analysisData.advanced_analysis.hazard_spectrum);
    }
    
    // Display disaggregation results if available
    if (analysisData.advanced_analysis && analysisData.advanced_analysis.disaggregation) {
        // Implement disaggregation visualization if needed
        console.log("Disaggregation data available:", analysisData.advanced_analysis.disaggregation);
    }
}
}