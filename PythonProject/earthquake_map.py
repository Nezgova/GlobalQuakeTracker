import requests
import folium
import pandas as pd
from datetime import datetime
import os
from geopy.distance import geodesic
import schedule
import time
import threading


# Function to fetch earthquake data from USGS API
def fetch_earthquake_data(time_period='hour'):
    """
    Fetch earthquake data from USGS API

    Parameters:
    time_period (str): Time period for which to fetch data ('hour', 'day', 'week', 'month')

    Returns:
    dict: JSON response from USGS API
    """
    base_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"
    url = f"{base_url}/all_{time_period}.geojson"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching earthquake data: {e}")
        return None


# Function to determine the marker color based on earthquake magnitude
def get_marker_color(magnitude):
    """
    Determine marker color based on earthquake magnitude

    Parameters:
    magnitude (float): Earthquake magnitude

    Returns:
    str: Color code
    """
    if magnitude < 4.0:
        return 'green'  # Weak
    elif magnitude < 6.0:
        return 'orange'  # Moderate
    else:
        return 'red'  # Strong


# Create a folium map with earthquake data
def create_earthquake_map(data, user_location=None):
    """
    Create a folium map with earthquake data

    Parameters:
    data (dict): Earthquake data from USGS API
    user_location (tuple): User's location as (latitude, longitude)

    Returns:
    folium.Map: Map with earthquake markers
    """
    # Start with user location if provided, otherwise global view
    initial_location = user_location if user_location else [0, 0]
    zoom_start = 6 if user_location else 2

    earthquake_map = folium.Map(location=initial_location, zoom_start=zoom_start)

    # Add user marker if location is provided
    if user_location:
        folium.Marker(
            location=user_location,
            popup="Your Location",
            icon=folium.Icon(color="blue", icon="user", prefix="fa")
        ).add_to(earthquake_map)

        # Add 100km radius circle around user location
        folium.Circle(
            location=user_location,
            radius=100000,  # 100km in meters
            color="blue",
            fill=True,
            fill_opacity=0.1,
            popup="100km Radius"
        ).add_to(earthquake_map)

    # Deduplicate earthquakes by ID
    processed_ids = set()

    for feature in data['features']:
        eq_id = feature['id']

        # Skip if already processed
        if eq_id in processed_ids:
            continue

        processed_ids.add(eq_id)

        properties = feature['properties']
        coordinates = feature['geometry']['coordinates']

        # Skip entries with null magnitude
        if properties['mag'] is None:
            continue

        longitude = coordinates[0]
        latitude = coordinates[1]
        depth = coordinates[2]
        magnitude = properties['mag']
        place = properties['place'] or "Unknown location"
        time_str = datetime.fromtimestamp(properties['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')

        # Calculate distance from user if location provided
        distance_info = ""
        if user_location:
            distance = geodesic(user_location, (latitude, longitude)).kilometers
            distance_info = f"<b>Distance from you:</b> {distance:.1f} km<br>"

        popup_text = f"""
        <b>Location:</b> {place}<br>
        <b>Magnitude:</b> {magnitude}<br>
        <b>Depth:</b> {depth} km<br>
        <b>Time:</b> {time_str}<br>
        {distance_info}
        """

        folium.CircleMarker(
            location=[latitude, longitude],
            radius=magnitude * 2,
            color=get_marker_color(magnitude),
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(earthquake_map)

    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 150px; height: 120px; 
                border:2px solid grey; z-index:9999; background-color:white;
                padding: 10px;
                font-size: 14px;
                ">
      <p style="margin-bottom: 5px"><b>Magnitude</b></p>
      <p><i class="fa fa-circle" style="color:green"></i> &lt; 4.0 (Weak)</p>
      <p><i class="fa fa-circle" style="color:orange"></i> 4.0-5.9 (Moderate)</p>
      <p><i class="fa fa-circle" style="color:red"></i> &gt;= 6.0 (Strong)</p>
    </div>
    '''
    earthquake_map.get_root().html.add_child(folium.Element(legend_html))

    return earthquake_map


# Save the earthquake map to an HTML file
def save_map(earthquake_map, output_dir='output', filename='earthquake_map.html'):
    """
    Save the earthquake map to an HTML file

    Parameters:
    earthquake_map (folium.Map): Map to save
    output_dir (str): Directory to save the map
    filename (str): Filename for the saved map
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    earthquake_map.save(output_path)
    print(f"Map saved to {output_path}")
    return output_path


# Function to find nearby earthquakes based on user's location
def find_nearby_earthquakes(user_lat, user_lon, earthquake_data, radius_km=100):
    """
    Find earthquakes near the user's location

    Parameters:
    user_lat (float): User's latitude
    user_lon (float): User's longitude
    earthquake_data (dict): Earthquake data from USGS API
    radius_km (float): Search radius in kilometers

    Returns:
    list: List of nearby earthquakes with details
    """
    nearby_earthquakes = []
    user_location = (user_lat, user_lon)

    # Deduplicate earthquakes
    processed_ids = set()

    for feature in earthquake_data['features']:
        eq_id = feature['id']

        # Skip if already processed
        if eq_id in processed_ids:
            continue

        processed_ids.add(eq_id)

        coordinates = feature['geometry']['coordinates']
        properties = feature['properties']

        # Skip entries with null magnitude
        if properties['mag'] is None:
            continue

        magnitude = properties['mag']
        place = properties['place'] or "Unknown location"
        time_str = datetime.fromtimestamp(properties['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        lat, lon = coordinates[1], coordinates[0]

        eq_location = (lat, lon)
        distance = geodesic(user_location, eq_location).kilometers

        # Check if earthquake is within specified radius
        if distance <= radius_km:
            nearby_earthquakes.append({
                "id": eq_id,
                "place": place,
                "magnitude": magnitude,
                "distance": distance,
                "time": time_str,
                "depth": coordinates[2]
            })

    # Sort by distance
    nearby_earthquakes.sort(key=lambda x: x["distance"])

    return nearby_earthquakes


# Function to update the map with new data
def update_map(time_period='hour', user_location=None):
    """
    Update the map with new earthquake data

    Parameters:
    time_period (str): Time period for which to fetch data
    user_location (tuple): User's location as (latitude, longitude)

    Returns:
    str: Path to the saved map file
    """
    print(f"Fetching new earthquake data for the past {time_period}...")
    earthquake_data = fetch_earthquake_data(time_period)

    if earthquake_data and earthquake_data.get('features'):
        print(f"Found {len(earthquake_data['features'])} earthquakes.")
        earthquake_map = create_earthquake_map(earthquake_data, user_location)
        return save_map(earthquake_map)
    else:
        print("No earthquake data found or error fetching data.")
        return None


# Function to run scheduled updates in a separate thread
def run_scheduler(time_period='hour', update_interval=10, user_location=None):
    """
    Run scheduled map updates in a separate thread

    Parameters:
    time_period (str): Time period for which to fetch data
    update_interval (int): Update interval in minutes
    user_location (tuple): User's location as (latitude, longitude)
    """

    def update_job():
        update_map(time_period, user_location)

    schedule.every(update_interval).minutes.do(update_job)

    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    """
    Main function to run the earthquake monitoring system
    """
    print("=== Earthquake Monitoring System ===")

    # Ask for user location
    use_location = input("Do you want to provide your location? (y/n): ").lower() == 'y'
    user_location = None

    if use_location:
        try:
            user_lat = float(input("Enter your latitude: "))
            user_lon = float(input("Enter your longitude: "))
            user_location = (user_lat, user_lon)

            # Initial fetch of data
            print("Fetching earthquake data...")
            earthquake_data = fetch_earthquake_data('day')

            if earthquake_data:
                # Find nearby earthquakes
                nearby_earthquakes = find_nearby_earthquakes(user_lat, user_lon, earthquake_data)

                if nearby_earthquakes:
                    print(f"\nFound {len(nearby_earthquakes)} earthquakes within 100km of your location:")
                    for i, eq in enumerate(nearby_earthquakes, 1):
                        print(
                            f"{i}. {eq['place']} - Magnitude: {eq['magnitude']:.1f}, Distance: {eq['distance']:.1f} km, Time: {eq['time']}")
                else:
                    print("No earthquakes found within 100km of your location.")
        except ValueError:
            print("Invalid coordinates. Using global view.")
            user_location = None

    # Time period selection
    print("\nSelect time period for earthquake data:")
    print("1. Past hour")
    print("2. Past day")
    print("3. Past week")
    print("4. Past month")

    choice = input("Enter your choice (1-4): ")
    time_periods = {"1": "hour", "2": "day", "3": "week", "4": "month"}
    time_period = time_periods.get(choice, "day")

    # Update interval
    update_interval = 60
    try:
        update_interval = int(input("\nEnter update interval in minutes (default: 60): ") or "60")
        update_interval = max(10, min(1440, update_interval))  # Between 10 minutes and 24 hours
    except ValueError:
        print("Invalid input. Using default interval of 60 minutes.")

    # Generate initial map
    map_path = update_map(time_period, user_location)
    if map_path:
        print(f"\nInitial map created. Open {map_path} in your web browser to view.")

        # Start scheduled updates in a separate thread
        print(f"\nStarting scheduled updates every {update_interval} minutes.")
        print("Press Ctrl+C to stop the program.")

        scheduler_thread = threading.Thread(
            target=run_scheduler,
            args=(time_period, update_interval, user_location)
        )
        scheduler_thread.daemon = True
        scheduler_thread.start()

        try:
            # Keep main thread alive to handle KeyboardInterrupt
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nProgram stopped by user.")
    else:
        print("Failed to create initial map. Please check your internet connection and try again.")


if __name__ == "__main__":
    main()