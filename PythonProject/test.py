import os
import requests
import folium
import schedule
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Advanced geospatial and data processing libraries
import numpy as np
import pandas as pd
from geopy.distance import geodesic
from rich.console import Console
from rich.table import Table
from transformers import pipeline
import plotly.express as px
import plotly.graph_objs as go

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('earthquake_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
console = Console()


class AdvancedEarthquakeTracker:
    """
    Comprehensive earthquake tracking and analysis application
    with advanced features and robust error handling.
    """

    # Enhanced API configuration with multiple sources
    EARTHQUAKE_APIS = {
        "USGS_PAST_DAY": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
        "USGS_SIGNIFICANT": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_day.geojson"
    }

    def __init__(self, user_lat: float = 0, user_lon: float = 0, radius_km: int = 100):
        """
        Initialize the earthquake tracker with user location and parameters.

        :param user_lat: User's latitude
        :param user_lon: User's longitude
        :param radius_km: Radius to check for nearby earthquakes
        """
        self.user_location = (user_lat, user_lon)
        self.radius_km = radius_km
        self.earthquake_data = None

        # Initialize chatbot with more advanced model
        self.chatbot = pipeline("text-generation", model="microsoft/DialoGPT-large")

    def fetch_earthquake_data(self, api_key: str = None) -> Optional[Dict]:
        """
        Fetch earthquake data with advanced error handling and optional API key support.

        :param api_key: Optional API key for authenticated requests
        :return: Parsed JSON earthquake data or None
        """
        headers = {"User-Agent": "EarthquakeTracker/1.0"} if api_key else {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        for name, url in self.EARTHQUAKE_APIS.items():
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                data = response.json()
                if data and "features" in data:
                    logger.info(f"Successfully fetched data from {name}")
                    return data

            except requests.exceptions.RequestException as e:
                logger.warning(f"Error fetching data from {name}: {e}")

        logger.error("Failed to fetch earthquake data from all sources")
        return None

    def analyze_earthquake_data(self) -> pd.DataFrame:
        """
        Transform raw earthquake data into a structured pandas DataFrame for analysis.

        :return: DataFrame with earthquake information
        """
        if not self.earthquake_data:
            self.earthquake_data = self.fetch_earthquake_data()

        if not self.earthquake_data:
            return pd.DataFrame()

        earthquakes = []
        for feature in self.earthquake_data.get("features", []):
            coords = feature["geometry"]["coordinates"]
            properties = feature["properties"]

            earthquakes.append({
                "latitude": coords[1],
                "longitude": coords[0],
                "magnitude": properties.get("mag", 0),
                "place": properties.get("place", "Unknown"),
                "time": datetime.fromtimestamp(properties.get("time", 0) / 1000),
                "depth": coords[2] if len(coords) > 2 else 0
            })

        return pd.DataFrame(earthquakes)

    def create_interactive_map(self, output_dir: str = '.') -> str:
        """
        Generate an advanced interactive map with Plotly.

        :param output_dir: Directory to save the map
        :return: Path to the generated map
        """
        df = self.analyze_earthquake_data()

        # Ensure magnitudes are non-negative for the size property
        df['magnitude'] = df['magnitude'].apply(lambda x: max(x, 0))  # Set negative magnitudes to 0

        fig = px.scatter_geo(
            df,
            lat='latitude',
            lon='longitude',
            color='magnitude',
            size='magnitude',
            hover_name='place',
            color_continuous_scale='Viridis',
            projection='natural earth'
        )

        output_path = os.path.join(output_dir, 'earthquake_map.html')
        fig.write_html(output_path)

        logger.info(f"Interactive map saved to {output_path}")
        return output_path  # This return statement is correctly indented


    def find_nearby_earthquakes(self) -> List[Dict]:
        """
        Enhanced nearby earthquake detection with more details.

        :return: List of nearby earthquake details
        """
        df = self.analyze_earthquake_data()

        nearby_quakes = []
        for _, row in df.iterrows():
            distance = geodesic(self.user_location, (row['latitude'], row['longitude'])).kilometers

            if distance <= self.radius_km:
                nearby_quakes.append({
                    "place": row['place'],
                    "magnitude": row['magnitude'],
                    "distance": distance,
                    "depth": row['depth'],
                    "time": row['time']
                })

        return sorted(nearby_quakes, key=lambda x: x['distance'])

    def display_nearby_earthquakes(self):
        """
        Rich-formatted display of nearby earthquakes.
        """
        nearby_quakes = self.find_nearby_earthquakes()

        if not nearby_quakes:
            console.print("[green]No recent earthquakes near your location.[/green]")
            return

        table = Table(title="Nearby Earthquakes")
        table.add_column("Place", style="cyan")
        table.add_column("Magnitude", style="magenta")
        table.add_column("Distance (km)", style="green")
        table.add_column("Depth (km)", style="yellow")
        table.add_column("Time", style="blue")

        for quake in nearby_quakes:
            table.add_row(
                str(quake['place']),
                f"{quake['magnitude']:.1f}",
                f"{quake['distance']:.2f}",
                f"{quake['depth']:.1f}",
                quake['time'].strftime("%Y-%m-%d %H:%M")
            )

        console.print(table)

    def start_background_updates(self, interval_minutes: int = 5):
        """
        Start scheduled background updates for earthquake data.

        :param interval_minutes: Update interval in minutes
        """

        def update_task():
            while True:
                try:
                    logger.info("Fetching earthquake data for background update...")
                    self.fetch_earthquake_data()
                    self.create_interactive_map()
                    logger.info(f"Background update complete, waiting {interval_minutes} minutes for next update.")
                    time.sleep(interval_minutes * 60)
                except Exception as e:
                    logger.error(f"Background update error: {e}")
                    time.sleep(interval_minutes * 60)

        update_thread = threading.Thread(target=update_task, daemon=True)
        update_thread.start()

    def interactive_chat(self):
        """
        Enhanced interactive chatbot with earthquake-related context.
        """
        console.print("[bold green]🌍 Earthquake Chatbot Activated![/bold green]")
        console.print("[dim]Type 'exit' to quit, 'quakes' for nearby earthquakes[/dim]")

        while True:
            user_input = input("You: ")

            if user_input.lower() in ['exit', 'quit']:
                break
            elif user_input.lower() == 'quakes':
                self.display_nearby_earthquakes()
                continue

            try:
                # Ensure the user input is valid before passing to the chatbot
                if user_input.strip():
                    response = self.chatbot(user_input)
                    console.print(f"[bold blue]Bot:[/bold blue] {response[0]['generated_text']}")
                else:
                    console.print("[red]Please enter a valid message.[/red]")
            except Exception as e:
                logger.error(f"Chatbot error: {e}")
                console.print("[red]Sorry, I couldn't process that message.[/red]")


def main():
    console.print("[bold green]🌍 Advanced Earthquake Tracker[/bold green]")

    try:
        user_lat = float(input("Enter your latitude: "))
        user_lon = float(input("Enter your longitude: "))

        tracker = AdvancedEarthquakeTracker(user_lat, user_lon)

        # Initial data fetch and map creation
        tracker.fetch_earthquake_data()
        tracker.create_interactive_map()
        tracker.display_nearby_earthquakes()

        # Start background updates
        tracker.start_background_updates()

        # Start interactive chat
        tracker.interactive_chat()

    except Exception as e:
        logger.error(f"Application error: {e}")
        console.print(f"[red]An error occurred: {e}[/red]")

if __name__ == "__main__":
    main()
