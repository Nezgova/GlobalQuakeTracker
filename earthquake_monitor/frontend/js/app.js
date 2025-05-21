
// Base URL for API requests - change this if your server is running on a different port/host
const API_BASE_URL = 'http://localhost:5000/api'

// Add a global error handler for API requests
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    if (event.reason && event.reason.message && event.reason.message.includes('Failed to fetch')) {
        alert('Unable to connect to the backend server. Please make sure the Flask server is running at ' + API_BASE_URL);
    }
});

// Map initialization
let map;
let markers = [];
let userMarker = null;
let selectedLocation = {
    lat: 0,
    lng: 0
};

// Store earthquake data
let earthquakeData = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    checkServerStatus();
    setupEventListeners();
    loadEarthquakes();
});

// Initialize Leaflet map
function initMap() {
    map = L.map('map').setView([20, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Add click handler to map
    map.on('click', function(e) {
        setUserLocation(e.latlng.lat, e.latlng.lng);
    });
}

// Set up event listeners for buttons
function setupEventListeners() {
    document.getElementById('filter-btn').addEventListener('click', loadEarthquakes);
    document.getElementById('analyze-btn').addEventListener('click', analyzeHazard);
    document.getElementById('report-btn').addEventListener('click', generateReport);
    document.getElementById('predict-btn').addEventListener('click', predictEarthquakes);
    
    // Location search handling using a simple solution
    document.getElementById('location').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchLocation();
        }
    });
}

// Check server status
function checkServerStatus() {
    fetch(`${API_BASE_URL}/status`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'online') {
                const lastUpdate = data.last_update ? new Date(data.last_update).toLocaleString() : 'unknown';
                document.getElementById('status').innerHTML = 
                    `Server online | Last update: ${lastUpdate} | 
                     Earthquakes loaded: ${data.earthquake_count}`;
            } else {
                document.getElementById('status').innerHTML = 'Server offline. Please try again later.';
            }
        })
        .catch(error => {
            console.error('Error checking server status:', error);
            document.getElementById('status').innerHTML = 'Error connecting to server. Make sure the backend is running at ' + API_BASE_URL;
        });
}

// Load earthquake data based on filters
function loadEarthquakes() {
    document.getElementById('spinner').style.display = 'block';
    
    const timePeriod = document.getElementById('time-period').value;
    const minMagnitude = document.getElementById('min-magnitude').value;
    
    let url = `${API_BASE_URL}/earthquakes?period=${timePeriod}&magnitude=${minMagnitude}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Check if the data has a 'features' array - GeoJSON format
            if (data && data.features && Array.isArray(data.features)) {
                earthquakeData = data.features;
            } else if (Array.isArray(data)) {
                earthquakeData = data;
            } else {
                console.error('Unexpected data format:', data);
                earthquakeData = [];
            }
            
            displayEarthquakes(earthquakeData);
            plotEarthquakesOnMap(earthquakeData);
            document.getElementById('spinner').style.display = 'none';
        })
        .catch(error => {
            console.error('Error loading earthquakes:', error);
            document.getElementById('spinner').style.display = 'none';
            document.getElementById('earthquake-data').innerHTML = 
                '<tr><td colspan="4">Error loading earthquake data</td></tr>';
        });
}

// Display earthquakes in the table
function displayEarthquakes(earthquakes) {
    const tableBody = document.getElementById('earthquake-data');
    tableBody.innerHTML = '';
    
    if (!earthquakes || earthquakes.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4">No earthquakes found</td></tr>';
        return;
    }
    
    // Make sure we're working with an array
    const quakeArray = Array.isArray(earthquakes) ? earthquakes : [];
    
    // Take only the first 50 earthquakes to display
    const displayQuakes = quakeArray.slice(0, 50);
    
    displayQuakes.forEach(quake => {
        try {
            // Skip if missing properties
            if (!quake.properties || !quake.geometry || !quake.geometry.coordinates) {
                console.log('Invalid earthquake structure:', quake);
                return;
            }
            
            const row = document.createElement('tr');
            
            const magnitudeCell = document.createElement('td');
            const magnitude = quake.properties.mag || 0;
            magnitudeCell.textContent = magnitude.toFixed(1);
            magnitudeCell.style.fontWeight = 'bold';
            
            // Color-code magnitude
            if (magnitude >= 6) {
                magnitudeCell.style.color = '#ff0000';
            } else if (magnitude >= 5) {
                magnitudeCell.style.color = '#ff6600';
            } else if (magnitude >= 4) {
                magnitudeCell.style.color = '#ffcc00';
            }
            
            const locationCell = document.createElement('td');
            locationCell.textContent = quake.properties.place || 'Unknown';
            
            const depthCell = document.createElement('td');
            depthCell.textContent = `${quake.geometry.coordinates[2].toFixed(1)} km`;
            
            const timeCell = document.createElement('td');
            timeCell.textContent = quake.properties.time ? 
                new Date(quake.properties.time).toLocaleString() : 'Unknown';
            
            row.appendChild(magnitudeCell);
            row.appendChild(locationCell);
            row.appendChild(depthCell);
            row.appendChild(timeCell);
            
            // Add click handler to zoom to earthquake
            row.style.cursor = 'pointer';
            row.addEventListener('click', () => {
                const coords = quake.geometry.coordinates;
                map.setView([coords[1], coords[0]], 8);
            });
            
            tableBody.appendChild(row);
        } catch (err) {
            console.error('Error displaying earthquake in table:', err);
        }
    });
}

// Plot earthquakes on the map
function plotEarthquakesOnMap(earthquakes) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    if (!earthquakes || earthquakes.length === 0) {
        console.log('No earthquake data to plot on map');
        return;
    }
    
    earthquakes.forEach(quake => {
        try {
            // Validate quake data
            if (!quake.geometry || !quake.geometry.coordinates || !quake.properties) {
                console.log('Invalid earthquake data structure:', quake);
                return;
            }
            
            const coords = quake.geometry.coordinates;
            const magnitude = quake.properties.mag || 0;
            
            // Size marker based on magnitude
            const radius = Math.max(5, magnitude * 2);
            
            // Color based on magnitude
            let color = '#1a9641'; // Green for small
            if (magnitude >= 6) {
                color = '#d7191c'; // Red for large
            } else if (magnitude >= 5) {
                color = '#fdae61'; // Orange for medium
            } else if (magnitude >= 4) {
                color = '#ffffbf'; // Yellow for moderate
            }
            
            const marker = L.circleMarker([coords[1], coords[0]], {
                radius: radius,
                fillColor: color,
                color: '#000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);
            
            marker.bindPopup(`
                <strong>Magnitude:</strong> ${magnitude}<br>
                <strong>Location:</strong> ${quake.properties.place || 'Unknown'}<br>
                <strong>Depth:</strong> ${coords[2]} km<br>
                <strong>Time:</strong> ${new Date(quake.properties.time).toLocaleString()}
            `);
            
            markers.push(marker);
        } catch (err) {
            console.error('Error plotting earthquake on map:', err);
        }
    });
}

// Set user's selected location
function setUserLocation(lat, lng) {
    selectedLocation.lat = lat;
    selectedLocation.lng = lng;
    
    // Update or create user marker
    if (userMarker) {
        map.removeLayer(userMarker);
    }
    
    userMarker = L.marker([lat, lng]).addTo(map);
    userMarker.bindPopup(`Selected Location: ${lat.toFixed(4)}, ${lng.toFixed(4)}`).openPopup();
}

// Search for a location using browser's geolocation API (simplified)
// In a real implementation, you'd use a geocoding service like Nominatim or Google Maps
function searchLocation() {
    const locationInput = document.getElementById('location').value;
    
    // This is a placeholder. In a real app, you'd use a geocoding service.
    // For now, we'll just show a message and suggest clicking on the map.
    alert(`To select "${locationInput}", please click directly on the map at the desired location.`);
}

// Analyze earthquake hazard at selected location
// Analyze earthquake hazard at selected location
function analyzeHazard() {
// Validate location first
if (selectedLocation.lat === 0 && selectedLocation.lng === 0) {
alert('Please select a location on the map first');
return;
}

// Show loading state
document.getElementById('spinner').style.display = 'block';
document.getElementById('analysis-results').innerHTML = 'Analyzing...';

// Get user input values
const radius = document.getElementById('radius').value || 300; // Default radius if not specified
const analysisType = document.getElementById('analysis-type').value || 'standard';

// Create request based on analysis type
// Remove the duplicated "api/" in the URL construction
let endpoint = `${API_BASE_URL}/analysis`;
const requestBody = {
latitude: selectedLocation.lat,
longitude: selectedLocation.lng,
radius: radius,
analysisType: analysisType
};

// Use appropriate endpoint for each analysis type
if (analysisType === 'advanced') {
// Optional: Could switch to dedicated endpoint
// endpoint = `${API_BASE_URL}/advanced-analysis`;
} else if (analysisType === 'summary') {
// Optional: Could switch to dedicated endpoint
// endpoint = `${API_BASE_URL}/hazard-summary`;
}

// Make API request
fetch(endpoint, {
method: 'POST',
headers: {
    'Content-Type': 'application/json'
},
body: JSON.stringify(requestBody)
})
.then(response => {
if (!response.ok) {
    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
}
return response.json();
})
.then(data => {
console.log("Received analysis data:", data); // Debug log
displayAnalysisResults(data);
})
.catch(error => {
console.error('Error performing analysis:', error);
document.getElementById('analysis-results').innerHTML = 
    `<div class="error-message">Error: ${error.message || 'Failed to perform analysis'}</div>`;
})
.finally(() => {
document.getElementById('spinner').style.display = 'none';
});
}

// Display hazard analysis results
function displayAnalysisResults(data) {
const resultsDiv = document.getElementById('analysis-results');

// Check for missing data
if (!data) {
resultsDiv.innerHTML = '<p>No analysis data received from server</p>';
return;
}

// Check for error messages from the server
if (data.error) {
resultsDiv.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
return;
}

// Display results based on analysis type
const analysisType = data.analysis_type || 'standard';

if (analysisType === 'summary') {
resultsDiv.innerHTML = `
    <h4>Hazard Summary</h4>
    <p><strong>Hazard Level:</strong> ${data.hazard_level || 'N/A'}</p>
    <p><strong>Recent Activity:</strong> ${data.recent_activity || 'N/A'}</p>
    <p>${data.summary || 'No summary available'}</p>
`;
} else if (analysisType === 'advanced') {
resultsDiv.innerHTML = `
    <h4>Advanced OpenQuake Analysis</h4>
    <p><strong>PGA (g):</strong> ${data.pga !== undefined ? data.pga.toFixed(4) : 'N/A'}</p>
    <p><strong>Annual Exceedance Probability:</strong> ${
        data.annual_exceedance_probability !== undefined ? 
        data.annual_exceedance_probability.toFixed(6) : 'N/A'
    }</p>
    <p><strong>Return Period:</strong> ${
        data.return_period !== undefined ?
        data.return_period.toFixed(1) + ' years' : 'N/A'
    }</p>
    <p><strong>Risk Level:</strong> ${data.risk_level || 'N/A'}</p>
    <p>${data.interpretation || 'No interpretation available'}</p>
`;

// If hazard curves data is available, we could render a chart here
if (data.hazard_curves && typeof renderHazardCurve === 'function') {
    renderHazardCurve(data.hazard_curves);
}
} else {
// Standard analysis - updated for actual server response format
resultsDiv.innerHTML = `
    <h4>Standard Hazard Analysis</h4>
    <p><strong>Earthquakes in region:</strong> ${data.nearby_earthquakes || 'N/A'}</p>
    <p><strong>Location:</strong> ${
        data.location ? 
        `${data.location.latitude.toFixed(4)}, ${data.location.longitude.toFixed(4)}` : 
        'N/A'
    }</p>
    <p><strong>Radius:</strong> ${
        data.location && data.location.radius_km ? 
        `${data.location.radius_km} km` : 
        'N/A'
    }</p>
    <p><strong>Risk level:</strong> ${data.risk_level || 'N/A'}</p>
    <p><strong>Probability:</strong> ${
        data.probability !== undefined ? 
        `${(data.probability * 100).toFixed(1)}%` : 
        'N/A'
    }</p>
    <p><strong>Analysis date:</strong> ${
        data.analysis_date ? 
        new Date(data.analysis_date).toLocaleString() : 
        'N/A'
    }</p>
`;

// Display nearest earthquakes if available in new format
if (data.recent_events && data.recent_events.length > 0) {
    resultsDiv.innerHTML += `
        <h5>Recent Significant Earthquakes:</h5>
        <ul class="earthquake-list">
            ${data.recent_events.map(eq => `
                <li>M${eq.magnitude.toFixed(1)} - ${eq.distance_km.toFixed(1)}km away 
                (${new Date(eq.time).toLocaleDateString()})</li>
            `).join('')}
        </ul>
    `;
}
}
}
// Generate PDF report
function generateReport() {
// Validate location selection
if (selectedLocation.lat === 0 && selectedLocation.lng === 0) {
alert('Please select a location on the map first');
return;
}

// Show loading spinner
const spinner = document.getElementById('spinner');
spinner.style.display = 'block';

// Get form values
const timePeriod = document.getElementById('time-period').value;
const minMagnitude = document.getElementById('min-magnitude').value;
const radius = document.getElementById('radius').value;
const analysisType = document.getElementById('analysis-type').value;
const reportTitle = `Earthquake Hazard Report - ${new Date().toLocaleDateString()}`;

// Create a status element for better user feedback
const statusElement = document.createElement('div');
statusElement.style.position = 'fixed';
statusElement.style.bottom = '20px';
statusElement.style.right = '20px';
statusElement.style.padding = '15px';
statusElement.style.backgroundColor = '#f8f9fa';
statusElement.style.border = '1px solid #dee2e6';
statusElement.style.borderRadius = '5px';
statusElement.style.zIndex = '1000';
statusElement.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
statusElement.innerHTML = `
<div style="display: flex; align-items: center; gap: 10px;">
    <div class="spinner-border text-primary" role="status" style="width: 1.5rem; height: 1.5rem;">
        <span class="visually-hidden">Loading...</span>
    </div>
    <div>
        <strong>Generating Report</strong>
        <div class="progress" style="height: 5px; width: 200px; margin-top: 5px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 100%"></div>
        </div>
    </div>
</div>
`;
document.body.appendChild(statusElement);

// Prepare the request data
const requestData = {
latitude: selectedLocation.lat,
longitude: selectedLocation.lng,
radius: radius,
timePeriod: timePeriod,
minMagnitude: minMagnitude,
analysisType: analysisType,
title: reportTitle
};

// Make the API request
fetch(`${API_BASE_URL}/report`, {
method: 'POST',
headers: {
    'Content-Type': 'application/json'
},
body: JSON.stringify(requestData)
})
.then(response => {
// Hide spinner immediately when we get any response
spinner.style.display = 'none';

if (!response.ok) {
    // Try to get error details from response
    return response.json().then(errorData => {
        throw new Error(errorData.error || `Server error: ${response.status} ${response.statusText}`);
    }).catch(() => {
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
    });
}

// Check content type to verify it's a PDF
const contentType = response.headers.get('content-type');
if (!contentType || !contentType.includes('application/pdf')) {
    return response.text().then(text => {
        try {
            const data = JSON.parse(text);
            if (data.error) {
                throw new Error(data.error);
            }
        } catch (e) {
            // Not JSON, just show the text
        }
        throw new Error('Server did not return a valid PDF file');
    });
}

return response.blob();
})
.then(blob => {
// Create download link
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = `earthquake_report_${selectedLocation.lat.toFixed(2)}_${selectedLocation.lng.toFixed(2)}.pdf`;
document.body.appendChild(a);
a.click();

// Clean up
window.URL.revokeObjectURL(url);
document.body.removeChild(a);

// Update status to success
statusElement.innerHTML = `
    <div style="display: flex; align-items: center; gap: 10px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="green" viewBox="0 0 16 16">
            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
        </svg>
        <div>
            <strong>Report Generated Successfully</strong>
            <div style="color: #6c757d; font-size: 0.9rem;">Download should start automatically</div>
        </div>
    </div>
`;

// Remove status element after delay
setTimeout(() => {
    statusElement.style.opacity = '0';
    setTimeout(() => document.body.removeChild(statusElement), 500);
}, 3000);
})
.catch(error => {
console.error('Error generating report:', error);
spinner.style.display = 'none';

// Update status to error
statusElement.innerHTML = `
    <div style="display: flex; align-items: center; gap: 10px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="red" viewBox="0 0 16 16">
            <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
        </svg>
        <div>
            <strong>Report Generation Failed</strong>
            <div style="color: #6c757d; font-size: 0.9rem;">${error.message}</div>
        </div>
    </div>
`;

// Remove status element after delay
setTimeout(() => {
    statusElement.style.opacity = '0';
    setTimeout(() => document.body.removeChild(statusElement), 500);
}, 5000);
});
}

// Helper function to download blob
function downloadBlob(blob, filename) {
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = filename;
document.body.appendChild(a);
a.click();
window.URL.revokeObjectURL(url);
document.body.removeChild(a);
}
// Helper function to download a blob
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Predict future earthquakes
function predictEarthquakes() {
    if (selectedLocation.lat === 0 && selectedLocation.lng === 0) {
        alert('Please select a location on the map first');
        return;
    }
    
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('prediction-results').innerHTML = 'Generating prediction...';
    
    const timeHorizon = document.getElementById('time-horizon').value;
    const intensityThreshold = document.getElementById('intensity-threshold').value;
    
    fetch(`${API_BASE_URL}/predict-earthquake`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            latitude: selectedLocation.lat,
            longitude: selectedLocation.lng,
            timeHorizon: timeHorizon,
            intensityThreshold: intensityThreshold
        })
    })
    .then(response => response.json())
    .then(data => {
        displayPredictionResults(data);
        document.getElementById('spinner').style.display = 'none';
    })
    .catch(error => {
        console.error('Error generating prediction:', error);
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('prediction-results').innerHTML = 'Error generating prediction';
    });
}

// Display earthquake prediction results
function displayPredictionResults(data) {
const resultsDiv = document.getElementById('prediction-results');

if (!data || !data.analysis_details) {
resultsDiv.innerHTML = '<p>No prediction data received from server</p>';
return;
}

const analysis = data.analysis_details;
const predictions = data.predictions || [];

// Estimate magnitude range from predictions
let minMag = null, maxMag = null;
if (predictions.length > 0) {
const magnitudes = predictions.map(p => p.estimated_magnitude);
minMag = Math.min(...magnitudes);
maxMag = Math.max(...magnitudes);
}

resultsDiv.innerHTML = `
<h4>Earthquake Prediction</h4>
<p><strong>Probability of significant earthquake:</strong> ${
    predictions.length > 0 ? (predictions[0].probability * 100).toFixed(2) + '%' : 'N/A'
}</p>
<p><strong>Expected magnitude range:</strong> ${
    minMag !== null && maxMag !== null ? minMag.toFixed(1) + ' - ' + maxMag.toFixed(1) : 'N/A'
}</p>
<p><strong>Confidence level:</strong> ${
    analysis.confidence_score ? (analysis.confidence_score * 100).toFixed(1) + '%' : 'N/A'
}</p>
<p><strong>Pattern:</strong> ${analysis.temporal_pattern || 'Unknown'}</p>
`;
}