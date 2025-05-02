/**
 * Chart visualization functionality
 */
class EarthquakeCharts {
    constructor() {
        this.magnitudeChart = null;
        this.initCharts();
    }

    /**
     * Initialize Chart.js charts
     */
    initCharts() {
        const ctx = document.getElementById('magnitude-chart').getContext('2d');
        
        // Create empty magnitude distribution chart
        this.magnitudeChart = new Chart(ctx, {
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
}