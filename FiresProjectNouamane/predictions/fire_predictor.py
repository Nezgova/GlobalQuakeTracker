# predictions/fire_predictor.py
import folium
import random
from datetime import datetime, timedelta


def simulate_fire_data(lat, lon, hours):
    fires = []
    for _ in range(random.randint(10, 50)):
        offset_lat = random.uniform(-1.0, 1.0)
        offset_lon = random.uniform(-1.0, 1.0)
        intensity = random.uniform(1.0, 10.0)
        timestamp = datetime.now() + timedelta(hours=random.randint(0, hours))
        fires.append({
            "lat": lat + offset_lat,
            "lon": lon + offset_lon,
            "intensity": intensity,
            "time": timestamp
        })
    return fires


def create_fire_map(fires, center_lat, center_lon, map_path):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    for fire in fires:
        folium.CircleMarker(
            location=[fire["lat"], fire["lon"]],
            radius=fire["intensity"],
            color="red",
            fill=True,
            fill_opacity=0.6,
            popup=f"🔥 Intensity: {fire['intensity']:.2f}\n🕒 {fire['time']}"
        ).add_to(m)
    m.save(map_path)


def save_predictions_to_txt(fires, text_path):
    with open(text_path, "w", encoding="utf-8") as f:
        for fire in fires:
            f.write(
                f"🔥 Fire at ({fire['lat']:.2f}, {fire['lon']:.2f}) - Intensity: {fire['intensity']:.2f} - Time: {fire['time']}\n")


def predict_fires(lat, lon, hours):
    fires = simulate_fire_data(lat, lon, hours)

    map_path = "predictions/fire_prediction_map.html"
    text_path = "predictions/fire_predictions.txt"

    create_fire_map(fires, lat, lon, map_path)
    save_predictions_to_txt(fires, text_path)

    return fires 