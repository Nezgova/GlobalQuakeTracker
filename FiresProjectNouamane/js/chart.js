// Configuration des graphiques
const chartConfig = {
    intensityChart: {
        type: 'line',
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Évolution de l\'Intensité des Incendies'
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Intensité'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Temps'
                    }
                }
            }
        }
    },
    probabilityChart: {
        type: 'bar',
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Probabilité d\'Incendie par Période'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Probabilité (%)'
                    }
                }
            }
        }
    },
    riskComparisonChart: {
        type: 'radar',
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Comparaison des Risques par Région'
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 10
                }
            }
        }
    }
};

// Initialisation des graphiques
function initCharts() {
    // Graphique d'intensité
    const intensityCtx = document.getElementById('intensity-chart').getContext('2d');
    window.intensityChart = new Chart(intensityCtx, {
        ...chartConfig.intensityChart,
        data: {
            labels: [],
            datasets: [{
                label: 'Intensité',
                data: [],
                borderColor: '#e67e22',
                tension: 0.4,
                fill: false
            }]
        }
    });
}

// Mise à jour des graphiques avec les nouvelles données
function updateCharts(fires) {
    // Mise à jour du graphique d'intensité
    const times = fires.map(fire => new Date(fire.time).toLocaleTimeString());
    const intensities = fires.map(fire => fire.intensity);
    
    window.intensityChart.data.labels = times;
    window.intensityChart.data.datasets[0].data = intensities;
    window.intensityChart.update();
    
    // Mise à jour des métriques
    updateMetrics(fires);
}

// Mise à jour des métriques
function updateMetrics(fires) {
    const totalFires = fires.length;
    const avgIntensity = fires.reduce((sum, fire) => sum + fire.intensity, 0) / totalFires;
    const strongestIntensity = Math.max(...fires.map(fire => fire.intensity));
    const recentFires = fires.filter(fire => {
        const fireTime = new Date(fire.time);
        const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
        return fireTime > oneHourAgo;
    }).length;
    
    document.getElementById('fire-count').textContent = totalFires;
    document.getElementById('avg-intensity').textContent = avgIntensity.toFixed(2);
    document.getElementById('strongest-intensity').textContent = strongestIntensity.toFixed(2);
    document.getElementById('recent-activity').textContent = recentFires;
}

// Mise à jour du graphique de probabilité
function updateProbabilityChart(probabilities) {
    if (!window.probabilityChart) {
        const ctx = document.getElementById('probability-time-chart').getContext('2d');
        window.probabilityChart = new Chart(ctx, {
            ...chartConfig.probabilityChart,
            data: {
                labels: ['Matin', 'Après-midi', 'Soir', 'Nuit'],
                datasets: [{
                    label: 'Probabilité',
                    data: probabilities,
                    backgroundColor: '#e67e22'
                }]
            }
        });
    } else {
        window.probabilityChart.data.datasets[0].data = probabilities;
        window.probabilityChart.update();
    }
}

// Mise à jour du graphique de comparaison des risques
function updateRiskComparisonChart(risks) {
    if (!window.riskComparisonChart) {
        const ctx = document.getElementById('risk-comparison-chart').getContext('2d');
        window.riskComparisonChart = new Chart(ctx, {
            ...chartConfig.riskComparisonChart,
            data: {
                labels: ['Nord', 'Sud', 'Est', 'Ouest', 'Centre'],
                datasets: [{
                    label: 'Niveau de Risque',
                    data: risks,
                    backgroundColor: 'rgba(230, 126, 34, 0.2)',
                    borderColor: '#e67e22',
                    pointBackgroundColor: '#e67e22'
                }]
            }
        });
    } else {
        window.riskComparisonChart.data.datasets[0].data = risks;
        window.riskComparisonChart.update();
    }
}

// Initialisation des graphiques au chargement
document.addEventListener('DOMContentLoaded', initCharts); 