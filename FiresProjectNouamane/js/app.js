// Configuration globale
const config = {
    apiEndpoint: '/api/fires',
    refreshInterval: 60000, // 1 minute
    itemsPerPage: 10
};

// État de l'application
let state = {
    currentFires: [],
    filteredFires: [],
    currentPage: 1,
    isLoading: false
};

// Initialisation de l'application
function initApp() {
    // Configuration des écouteurs d'événements
    setupEventListeners();
    
    // Chargement initial des données
    loadFireData();
    
    // Configuration du rafraîchissement automatique
    setInterval(loadFireData, config.refreshInterval);
}

// Configuration des écouteurs d'événements
function setupEventListeners() {
    // Filtres
    document.getElementById('min-intensity').addEventListener('input', function(e) {
        document.getElementById('min-intensity-value').textContent = e.target.value;
        filterFires();
    });
    
    document.getElementById('time-period').addEventListener('change', filterFires);
    document.getElementById('location-filter').addEventListener('change', filterFires);
    
    // Boutons
    document.getElementById('refresh-data').addEventListener('click', loadFireData);
    document.getElementById('generate-report').addEventListener('click', generateReport);
}

// Chargement des données d'incendie
async function loadFireData() {
    try {
        showLoading(true);
        
        const response = await fetch(config.apiEndpoint);
        if (!response.ok) throw new Error('Erreur lors du chargement des données');
        
        const fires = await response.json();
        state.currentFires = fires;
        filterFires();
        
    } catch (error) {
        console.error('Erreur:', error);
        showError('Impossible de charger les données. Veuillez réessayer.');
    } finally {
        showLoading(false);
    }
}

// Filtrage des incendies
function filterFires() {
    const minIntensity = parseFloat(document.getElementById('min-intensity').value);
    const timePeriod = document.getElementById('time-period').value;
    const location = document.getElementById('location-filter').value;
    
    state.filteredFires = state.currentFires.filter(fire => {
        // Filtre d'intensité
        if (fire.intensity < minIntensity) return false;
        
        // Filtre de période
        const fireTime = new Date(fire.time);
        const now = new Date();
        const timeDiff = now - fireTime;
        
        switch (timePeriod) {
            case 'hour':
                if (timeDiff > 60 * 60 * 1000) return false;
                break;
            case 'day':
                if (timeDiff > 24 * 60 * 60 * 1000) return false;
                break;
            case 'week':
                if (timeDiff > 7 * 24 * 60 * 60 * 1000) return false;
                break;
            case 'month':
                if (timeDiff > 30 * 24 * 60 * 60 * 1000) return false;
                break;
        }
        
        // Filtre de localisation
        if (location !== 'all') {
            // Logique de filtrage par région à implémenter
            // Pour l'instant, on retourne true
            return true;
        }
        
        return true;
    });
    
    state.currentPage = 1;
    updateUI();
}

// Mise à jour de l'interface
function updateUI() {
    // Mise à jour de la carte
    updateFireMarkers(state.filteredFires);
    
    // Mise à jour des graphiques
    updateCharts(state.filteredFires);
    
    // Mise à jour de la liste des incendies
    updateFireTable();
    
    // Mise à jour de la pagination
    updatePagination();
}

// Mise à jour du tableau des incendies
function updateFireTable() {
    const tbody = document.getElementById('fire-list');
    const start = (state.currentPage - 1) * config.itemsPerPage;
    const end = start + config.itemsPerPage;
    const pageFires = state.filteredFires.slice(start, end);
    
    tbody.innerHTML = pageFires.length ? pageFires.map(fire => `
        <tr>
            <td>${new Date(fire.time).toLocaleString()}</td>
            <td>${fire.intensity.toFixed(2)}</td>
            <td>${fire.lat.toFixed(4)}, ${fire.lon.toFixed(4)}</td>
            <td>${getFireStatus(fire.intensity)}</td>
        </tr>
    `).join('') : '<tr><td colspan="4">Aucun incendie trouvé</td></tr>';
    
    document.getElementById('fire-count-label').textContent = `(${state.filteredFires.length})`;
}

// Mise à jour de la pagination
function updatePagination() {
    const totalPages = Math.ceil(state.filteredFires.length / config.itemsPerPage);
    const pagination = document.getElementById('pagination-controls');
    
    let html = '';
    
    // Bouton précédent
    html += `
        <button onclick="changePage(${state.currentPage - 1})" 
                ${state.currentPage === 1 ? 'disabled' : ''}>
            Précédent
        </button>
    `;
    
    // Pages
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <button onclick="changePage(${i})" 
                    class="${i === state.currentPage ? 'active' : ''}">
                ${i}
            </button>
        `;
    }
    
    // Bouton suivant
    html += `
        <button onclick="changePage(${state.currentPage + 1})" 
                ${state.currentPage === totalPages ? 'disabled' : ''}>
            Suivant
        </button>
    `;
    
    pagination.innerHTML = html;
}

// Changement de page
function changePage(page) {
    if (page < 1 || page > Math.ceil(state.filteredFires.length / config.itemsPerPage)) return;
    state.currentPage = page;
    updateUI();
}

// Génération du rapport
async function generateReport() {
    try {
        showLoading(true);
        
        const response = await fetch('/api/generate-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fires: state.filteredFires,
                filters: {
                    minIntensity: document.getElementById('min-intensity').value,
                    timePeriod: document.getElementById('time-period').value,
                    location: document.getElementById('location-filter').value
                }
            })
        });
        
        if (!response.ok) throw new Error('Erreur lors de la génération du rapport');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'rapport_incendies.pdf';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        console.error('Erreur:', error);
        showError('Impossible de générer le rapport. Veuillez réessayer.');
    } finally {
        showLoading(false);
    }
}

// Affichage du chargement
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.toggle('active', show);
    state.isLoading = show;
}

// Affichage des erreurs
function showError(message) {
    // Implémentation de l'affichage des erreurs
    alert(message);
}

// Détermination du statut de l'incendie
function getFireStatus(intensity) {
    if (intensity < 3) return '<span class="text-success">Faible</span>';
    if (intensity < 6) return '<span class="text-warning">Modéré</span>';
    if (intensity < 8) return '<span class="text-danger">Élevé</span>';
    return '<span class="text-danger fw-bold">Critique</span>';
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', initApp); 