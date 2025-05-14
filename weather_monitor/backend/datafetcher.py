import requests
import datetime
import os
import json
import xml.etree.ElementTree as ET
from geopy.geocoders import Nominatim
import time

TSUNAMI_FEED_URL = "https://www.tsunami.gov/events/xml/PAAQ.xml"

def get_tsunami_data():
    """Fetch real-time tsunami alerts from NOAA and save them."""
    
    try:
        os.makedirs("data", exist_ok=True)
        today = datetime.date.today()
        output_file = f"data/tsunami_data_{today}.json"

        # Skip if already downloaded today
        if os.path.exists(output_file):
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(output_file))
            if file_time.date() == today:
                with open(output_file, 'r') as f:
                    return json.load(f)

        print("Fetching real-time tsunami alerts from NOAA...")
        response = requests.get(TSUNAMI_FEED_URL)
        alerts = []
        geolocator = Nominatim(user_agent="tsunami_monitor", timeout=10)

        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                try:
                    title = entry.find('{http://www.w3.org/2005/Atom}title').text
                    summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
                    updated = entry.find('{http://www.w3.org/2005/Atom}updated').text
                    # Try to extract location from the title or summary
                    location = "Unknown"
                    if '-' in title:
                        location = title.split('-')[-1].strip()
                    elif 'for' in summary:
                        location = summary.split('for')[-1].split('.')[0].strip()
                    # Geocode location if possible
                    lat, lon = None, None
                    if location != "Unknown":
                        try:
                            geo = geolocator.geocode(location, timeout=5)
                            if geo:
                                lat, lon = geo.latitude, geo.longitude
                        except Exception:
                            pass
                    alerts.append({
                        "city": location,
                        "country": "",
                        "lat": lat,
                        "lon": lon,
                        "level": title,
                        "value": 1,
                        "time": updated,
                        "description": summary,
                        "end_time": ""
                    })
                except Exception as e:
                    print(f"Error processing tsunami alert: {e}")
                    continue
        else:
            print(f"Failed to fetch tsunami feed: {response.status_code}")

        # Save the data
        with open(output_file, 'w') as f:
            json.dump(alerts, f)

        return alerts
    except Exception as e:
        print(f"Error in get_tsunami_data: {e}")
        return []

if __name__ == '__main__':
    print("Testing NOAA Tsunami feed fetch...")
    test_data = get_tsunami_data()
    print(f"\nFound {len(test_data)} tsunami alerts from NOAA feed")
    if test_data:
        print("\nSample alerts:")
        for alert in test_data[:10]:
            print(f"{alert['city']} - {alert['level']} at {alert['time']}")
