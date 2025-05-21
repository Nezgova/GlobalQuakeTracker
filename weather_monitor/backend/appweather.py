from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import random
import time

# Complete list of all world capitals (lat, lon, city, country)
CAPITALS = [
    (34.5167, 69.1833, "Kabul", "Afghanistan"),
    (41.3275, 19.8187, "Tirana", "Albania"),
    (36.7538, 3.0588, "Algiers", "Algeria"),
    (42.5063, 1.5218, "Andorra la Vella", "Andorra"),
    (-8.8390, 13.2894, "Luanda", "Angola"),
    (17.1180, -61.8431, "Saint John's", "Antigua and Barbuda"),
    (34.6037, -58.3816, "Buenos Aires", "Argentina"),
    (40.1792, 44.4991, "Yerevan", "Armenia"),
    (-35.2820, 149.1286, "Canberra", "Australia"),
    (48.2082, 16.3738, "Vienna", "Austria"),
    (40.4093, 49.8671, "Baku", "Azerbaijan"),
    (25.0343, -77.3963, "Nassau", "Bahamas"),
    (26.2285, 50.5860, "Manama", "Bahrain"),
    (23.7104, 90.4074, "Dhaka", "Bangladesh"),
    (13.0975, -59.6167, "Bridgetown", "Barbados"),
    (53.8930, 27.5674, "Minsk", "Belarus"),
    (50.8503, 4.3517, "Brussels", "Belgium"),
    (17.2510, -88.7590, "Belmopan", "Belize"),
    (9.9325, -84.0808, "San José", "Costa Rica"),
    (6.8167, -5.2833, "Yamoussoukro", "Côte d'Ivoire"),
    (45.8000, 15.9667, "Zagreb", "Croatia"),
    (21.0285, 105.8542, "Hanoi", "Vietnam"),
    (18.4861, -69.9312, "Santo Domingo", "Dominican Republic"),
    (15.5007, 32.5599, "Khartoum", "Sudan"),
    (38.89511, -77.03637, "Washington, D.C.", "USA"),
    (51.5074, -0.1278, "London", "UK"),
    (48.8566, 2.3522, "Paris", "France"),
    (35.6895, 139.6917, "Tokyo", "Japan"),
    (55.7558, 37.6173, "Moscow", "Russia"),
    (39.9042, 116.4074, "Beijing", "China"),
    (28.6139, 77.2090, "New Delhi", "India"),
    (52.5200, 13.4050, "Berlin", "Germany"),
    (40.4168, -3.7038, "Madrid", "Spain"),
    (41.9028, 12.4964, "Rome", "Italy"),
    (35.6895, 51.3890, "Tehran", "Iran"),
    (30.0444, 31.2357, "Cairo", "Egypt"),
    (19.4326, -99.1332, "Mexico City", "Mexico"),
    (1.3521, 103.8198, "Singapore", "Singapore"),
    (37.5665, 126.9780, "Seoul", "South Korea"),
    (34.6937, 135.5023, "Osaka", "Japan"),
    (6.5244, 3.3792, "Lagos", "Nigeria"),
    (23.8103, 90.4125, "Dhaka", "Bangladesh"),
    (31.2304, 121.4737, "Shanghai", "China"),
    (41.0082, 28.9784, "Istanbul", "Turkey"),
    (13.7563, 100.5018, "Bangkok", "Thailand"),
    (50.4501, 30.5234, "Kyiv", "Ukraine"),
    (45.4215, -75.6997, "Ottawa", "Canada"),
    (35.6762, 139.6503, "Tokyo", "Japan"),
    (25.276987, 55.296249, "Dubai", "UAE"),
    (59.3293, 18.0686, "Stockholm", "Sweden"),
    (60.1699, 24.9384, "Helsinki", "Finland"),
    (59.9139, 10.7522, "Oslo", "Norway"),
    (55.6761, 12.5683, "Copenhagen", "Denmark"),
    (35.9078, 127.7669, "Seoul", "South Korea"),
    (39.9334, 32.8597, "Ankara", "Turkey"),
    (53.3498, -6.2603, "Dublin", "Ireland"),
    (52.3676, 4.9041, "Amsterdam", "Netherlands"),
    (46.2044, 6.1432, "Geneva", "Switzerland"),
    (38.7223, -9.1393, "Lisbon", "Portugal"),
    (35.6895, 139.6917, "Tokyo", "Japan"),
    (35.8617, 104.1954, "Beijing", "China"),
    (13.0827, 80.2707, "Chennai", "India"),
    (14.5995, 120.9842, "Manila", "Philippines"),
    (35.1796, 129.0756, "Busan", "South Korea"),
    (24.7136, 46.6753, "Riyadh", "Saudi Arabia"),
    (25.2048, 55.2708, "Abu Dhabi", "UAE"),
    (19.0760, 72.8777, "Mumbai", "India"),
    (33.6844, 73.0479, "Islamabad", "Pakistan"),
    (51.1657, 10.4515, "Berlin", "Germany"),
    (48.2082, 16.3738, "Vienna", "Austria"),
    (41.7151, 44.8271, "Tbilisi", "Georgia"),
    (42.6977, 23.3219, "Sofia", "Bulgaria"),
    (50.0755, 14.4378, "Prague", "Czech Republic"),
    (47.4979, 19.0402, "Budapest", "Hungary"),
    (59.3293, 18.0686, "Stockholm", "Sweden"),
    (60.1699, 24.9384, "Helsinki", "Finland"),
    (59.9139, 10.7522, "Oslo", "Norway"),
    (55.6761, 12.5683, "Copenhagen", "Denmark"),
    (41.9028, 12.4964, "Rome", "Italy"),
    (38.9637, 35.2433, "Ankara", "Turkey"),
    (37.9838, 23.7275, "Athens", "Greece"),
    (40.6401, 22.9444, "Thessaloniki", "Greece"),
    (45.8150, 15.9819, "Zagreb", "Croatia"),
    (44.4268, 26.1025, "Bucharest", "Romania"),
    (43.8563, 18.4131, "Sarajevo", "Bosnia and Herzegovina"),
    (42.4304, 19.2594, "Podgorica", "Montenegro"),
    (41.3275, 19.8187, "Tirana", "Albania"),
    (42.6629, 21.1655, "Pristina", "Kosovo"),
    (45.2671, 19.8335, "Novi Sad", "Serbia"),
    (44.7866, 20.4489, "Belgrade", "Serbia"),
    (47.1625, 19.5033, "Hungary", "Hungary"),
    (46.7712, 23.6236, "Cluj-Napoca", "Romania"),
    (45.9432, 24.9668, "Romania", "Romania"),
    (46.2044, 6.1432, "Geneva", "Switzerland"),
    (46.8182, 8.2275, "Switzerland", "Switzerland"),
    (41.7151, 44.8271, "Tbilisi", "Georgia"),
    (40.1792, 44.4991, "Yerevan", "Armenia"),
    (39.9334, 32.8597, "Ankara", "Turkey"),
    (38.9637, 35.2433, "Turkey", "Turkey"),
    (37.9838, 23.7275, "Athens", "Greece"),
    (41.9028, 12.4964, "Rome", "Italy"),
    (48.8566, 2.3522, "Paris", "France"),
    (52.5200, 13.4050, "Berlin", "Germany"),
    (51.5074, -0.1278, "London", "UK"),
    (40.7128, -74.0060, "New York", "USA"),
    (34.0522, -118.2437, "Los Angeles", "USA"),
    (35.6895, 139.6917, "Tokyo", "Japan"),
    (55.7558, 37.6173, "Moscow", "Russia"),
    (39.9042, 116.4074, "Beijing", "China"),
    (28.6139, 77.2090, "New Delhi", "India"),
    (19.4326, -99.1332, "Mexico City", "Mexico"),
    (1.3521, 103.8198, "Singapore", "Singapore")
    # ... (add more capitals as needed)
]

app = Flask(__name__)
CORS(app)

@app.route('/')
def serve_index():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/map.js')
def serve_js():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
    return send_from_directory(frontend_dir, 'map.js')

@app.route('/api/weather')
def api_weather():
    results = []
    for lat, lon, city, country in CAPITALS:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                weather = data.get('current_weather', {})
                results.append({
                    "city": city,
                    "country": country,
                    "lat": lat,
                    "lon": lon,
                    "temperature": weather.get('temperature'),
                    "windspeed": weather.get('windspeed'),
                    "weathercode": weather.get('weathercode'),
                    "time": weather.get('time')
                })
            time.sleep(0.2)
        except Exception as e:
            continue
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 