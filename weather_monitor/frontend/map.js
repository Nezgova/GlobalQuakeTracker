// Weather code to color mapping
const WEATHER_COLORS = {
    clear: '#FFD600',      // yellow
    cloudy: '#B0BEC5',    // gray
    rain: '#2196F3',      // blue
    snow: '#90CAF9',      // light blue
    thunder: '#FF7043',   // orange
    wind: '#00C853',      // green
    fog: '#8D6E63',       // brown
    unknown: '#757575'    // dark gray
};

// Weather type to background image mapping
const WEATHER_BG = {
    clear: 'sun.png',
    cloudy: 'cloudy.png',
    rain: 'rain.png',
    snow: 'snow.png',
    thunder: 'thunder.png',
    wind: 'windy.png',
    fog: 'fog.png',
    unknown: 'cloudy.png'
};

// Weather code to type mapping (Open-Meteo codes)
function getWeatherType(code, windspeed) {
    if (windspeed && windspeed > 40) return 'wind';
    if ([0, 1].includes(code)) return 'clear';
    if ([2, 3].includes(code)) return 'cloudy';
    if ([45, 48].includes(code)) return 'fog';
    if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return 'rain';
    if ([71, 73, 75, 77, 85, 86].includes(code)) return 'snow';
    if ([95, 96, 99].includes(code)) return 'thunder';
    return 'unknown';
}

// Weather type to emoji
const WEATHER_EMOJI = {
    clear: '☀️',
    cloudy: '☁️',
    rain: '🌧️',
    snow: '❄️',
    thunder: '⛈️',
    wind: '💨',
    fog: '🌫️',
    unknown: '❔'
};

// Add legend to the map
function addLegend() {
    const legend = document.createElement('div');
    legend.id = 'weather-legend';
    legend.style.background = '#222';
    legend.style.color = '#fff';
    legend.style.padding = '8px 16px';
    legend.style.borderRadius = '8px';
    legend.style.position = 'absolute';
    legend.style.top = '20px';
    legend.style.left = '50%';
    legend.style.transform = 'translateX(-50%)';
    legend.style.zIndex = 1000;
    legend.style.display = 'flex';
    legend.style.gap = '18px';
    legend.innerHTML = `
      <span><span style="background:${WEATHER_COLORS.clear};width:16px;height:16px;display:inline-block;border-radius:50%;margin-right:6px;"></span>Clear</span>
      <span><span style="background:${WEATHER_COLORS.cloudy};width:16px;height:16px;display:inline-block;border-radius:50%;margin-right:6px;"></span>Cloudy</span>
      <span><span style="background:${WEATHER_COLORS.rain};width:16px;height:16px;display:inline-block;border-radius:50%;margin-right:6px;"></span>Rain</span>
      <span><span style="background:${WEATHER_COLORS.snow};width:16px;height:16px;display:inline-block;border-radius:50%;margin-right:6px;"></span>Snow</span>
      <span><span style="background:${WEATHER_COLORS.thunder};width:16px;height:16px;display:inline-block;border-radius:50%;margin-right:6px;"></span>Thunder</span>
      <span><span style="background:${WEATHER_COLORS.wind};width:16px;height:16px;display:inline-block;border-radius:50%;margin-right:6px;"></span>Windy</span>
      <span><span style="background:${WEATHER_COLORS.fog};width:16px;height:16px;display:inline-block;border-radius:50%;margin-right:6px;"></span>Fog</span>
    `;
    document.body.appendChild(legend);
}

// Initialize map
const map = L.map('map').setView([20, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

addLegend();

let markers = [];

// DOM elements
const refreshBtn = document.getElementById('refreshBtn');
const exportBtn = document.getElementById('exportBtn');
const weatherCards = document.getElementById('weatherCards');

// Event listeners
refreshBtn.addEventListener('click', loadWeatherData);
exportBtn.addEventListener('click', () => {
    alert('Export functionality coming soon');
});

// Main data loading function
async function loadWeatherData() {
    try {
        showLoading();
        const response = await fetch('/api/weather');
        if (!response.ok) throw new Error('Failed to fetch data');
        const data = await response.json();
        if (!data || data.length === 0) {
            showNoData();
            return;
        }
        updateMap(data);
        updateCards(data);
    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    }
}

function updateMap(data) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    // Add new markers
    data.forEach(location => {
        const type = getWeatherType(location.weathercode, location.windspeed);
        const color = WEATHER_COLORS[type] || WEATHER_COLORS.unknown;
        if (location.lat && location.lon) {
            const marker = L.circleMarker([location.lat, location.lon], {
                radius: 8,
                fillColor: color,
                color: '#fff',
                weight: 1,
                fillOpacity: 0.8
            }).addTo(map);
            marker.bindPopup(`
                <b>${location.city}, ${location.country}</b><br>
                Date/Time: ${location.time}<br>
                Temp: ${location.temperature} °C<br>
                Wind: ${location.windspeed} km/h
            `);
            markers.push(marker);
        }
    });
    // Auto-zoom to show all markers
    if (markers.length > 0) {
        const markerGroup = new L.featureGroup(markers);
        map.fitBounds(markerGroup.getBounds().pad(0.2));
    }
}

function updateCards(data) {
    weatherCards.innerHTML = '';
    data.forEach(location => {
        const type = getWeatherType(location.weathercode, location.windspeed);
        const emoji = WEATHER_EMOJI[type] || WEATHER_EMOJI.unknown;
        const color = WEATHER_COLORS[type] || WEATHER_COLORS.unknown;
        const bg = WEATHER_BG[type] || WEATHER_BG.unknown;
        const card = document.createElement('div');
        card.className = 'weather-card';
        card.style.borderColor = color;
        card.style.background = `url('${bg}') center/cover no-repeat, var(--card-dark)`;
        card.innerHTML = `
            <div class="city">${location.city}</div>
            <div class="country">${location.country}</div>
            <div class="temp">${location.temperature !== undefined ? location.temperature + '°C' : '--'}</div>
            <div class="weather"><span style="font-size:1.5em;">${emoji}</span> <span>${type.charAt(0).toUpperCase() + type.slice(1)}</span></div>
            <div class="wind">💨 ${location.windspeed !== undefined ? location.windspeed + ' km/h' : '--'}</div>
            <div class="time">${location.time || ''}</div>
        `;
        weatherCards.appendChild(card);
    });
}

function showLoading() {
    weatherCards.innerHTML = `<div class="loading">Loading data...</div>`;
}

function showNoData() {
    weatherCards.innerHTML = `<div class="loading">No weather data found</div>`;
}

function showError(message) {
    weatherCards.innerHTML = `<div class="error">Error: ${message}</div>`;
}

// Initial load
loadWeatherData(); 