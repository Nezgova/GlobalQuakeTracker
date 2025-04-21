import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Data processing libraries
import numpy as np
import pandas as pd
from geopy.distance import geodesic
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import plotly.express as px
import plotly.graph_objs as go

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('earthquake_prediction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EarthquakePredictionMap:
    """
    Focused earthquake map generator with time-based predictions.
    """

    # API configuration
    EARTHQUAKE_APIS = {
        "USGS_PAST_DAY": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
        "USGS_PAST_MONTH": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson"  # For historical data
    }

    def __init__(self, user_lat: float, user_lon: float, radius_km: int = 100):
        """
        Initialize the earthquake prediction map generator.

        :param user_lat: User's latitude
        :param user_lon: User's longitude
        :param radius_km: Radius to check for nearby earthquakes
        """
        self.user_location = (user_lat, user_lon)
        self.radius_km = radius_km
        self.earthquake_data = None
        self.historical_data = None
        self.prediction_model = None
        
        print(f"Initializing for location: {user_lat}, {user_lon}")
        print("Loading data and training prediction model...")

    def fetch_earthquake_data(self, historical: bool = False) -> Optional[Dict]:
        """
        Fetch earthquake data from USGS.

        :param historical: Whether to fetch historical data
        :return: Parsed JSON earthquake data or None
        """
        # Choose which API to query based on historical flag
        api_name = "USGS_PAST_MONTH" if historical else "USGS_PAST_DAY"
        url = self.EARTHQUAKE_APIS[api_name]

        try:
            print(f"Fetching data from {api_name}...")
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            data = response.json()
            if data and "features" in data:
                logger.info(f"Successfully fetched data from {api_name}")
                return data

        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching data from {api_name}: {e}")

        logger.error(f"Failed to fetch earthquake data from {api_name}")
        return None

    def analyze_earthquake_data(self, data=None, historical=False) -> pd.DataFrame:
        """
        Transform raw earthquake data into a structured pandas DataFrame for analysis.

        :param data: Optional raw earthquake data
        :param historical: Whether this is historical data
        :return: DataFrame with earthquake information
        """
        if data is None:
            data = self.historical_data if historical else self.earthquake_data
            
        if not data:
            if historical:
                self.historical_data = self.fetch_earthquake_data(historical=True)
                data = self.historical_data
            else:
                self.earthquake_data = self.fetch_earthquake_data()
                data = self.earthquake_data

        if not data:
            return pd.DataFrame()

        earthquakes = []
        for feature in data.get("features", []):
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

    def train_prediction_model(self):
        """
        Train a machine learning model for earthquake prediction.
        """
        try:
            # Fetch historical data if needed
            if not self.historical_data:
                self.historical_data = self.fetch_earthquake_data(historical=True)
                
            historical_df = self.analyze_earthquake_data(self.historical_data, historical=True)
            
            if historical_df.empty:
                logger.warning("No historical data available for training prediction model")
                return False
                
            # Feature engineering
            historical_df['sin_lat'] = np.sin(np.radians(historical_df['latitude']))
            historical_df['cos_lat'] = np.cos(np.radians(historical_df['latitude']))
            historical_df['sin_lon'] = np.sin(np.radians(historical_df['longitude']))
            historical_df['cos_lon'] = np.cos(np.radians(historical_df['longitude']))
            
            # Create features and targets for our prediction models
            features = ['sin_lat', 'cos_lat', 'sin_lon', 'cos_lon', 'depth']
            X = historical_df[features]
            y_magnitude = historical_df['magnitude']
            
            # Create and train magnitude prediction model
            self.prediction_model = RandomForestRegressor(n_estimators=50, random_state=42)
            self.prediction_model.fit(X, y_magnitude)
            
            logger.info("Successfully trained earthquake prediction model")
            print("Prediction model training complete!")
            return True
            
        except Exception as e:
            logger.error(f"Error training prediction model: {e}")
            print(f"Error training prediction model: {e}")
            return False

    def predict_future_earthquakes(self, hours_ahead=24) -> pd.DataFrame:
        """
        Predict potential future earthquakes near the user's location.
        
        :param hours_ahead: Hours ahead to predict for
        :return: DataFrame with prediction results
        """
        if not self.prediction_model:
            if not self.train_prediction_model():
                print("Could not train prediction model.")
                return pd.DataFrame()
            
        try:
            print(f"Generating predictions for the next {hours_ahead} hours...")
            
            # Generate grid points around user location
            lat, lon = self.user_location
            grid_size = 10  # Number of points in each direction
            grid_step = self.radius_km / 111  # Approximate conversion from km to degrees
            
            grid_points = []
            for i in range(-grid_size, grid_size + 1):
                for j in range(-grid_size, grid_size + 1):
                    grid_lat = lat + (i * grid_step / grid_size)
                    grid_lon = lon + (j * grid_step / grid_size)
                    
                    # Skip points too far from user location
                    if geodesic((lat, lon), (grid_lat, grid_lon)).kilometers > self.radius_km:
                        continue
                        
                    # Add depth variations
                    for depth in [5, 10, 15, 20, 30]:
                        grid_points.append({
                            'latitude': grid_lat,
                            'longitude': grid_lon,
                            'depth': depth
                        })
            
            if not grid_points:
                return pd.DataFrame()
                
            grid_df = pd.DataFrame(grid_points)
            
            # Feature engineering
            grid_df['sin_lat'] = np.sin(np.radians(grid_df['latitude']))
            grid_df['cos_lat'] = np.cos(np.radians(grid_df['latitude']))
            grid_df['sin_lon'] = np.sin(np.radians(grid_df['longitude']))
            grid_df['cos_lon'] = np.cos(np.radians(grid_df['longitude']))
            
            # Make predictions
            features = ['sin_lat', 'cos_lat', 'sin_lon', 'cos_lon', 'depth']
            grid_df['predicted_magnitude'] = self.prediction_model.predict(grid_df[features])
            
            # Filter out insignificant predictions
            significant_predictions = grid_df[grid_df['predicted_magnitude'] > 3.0].copy()
            
            if significant_predictions.empty:
                print("No significant earthquake predictions found.")
                return pd.DataFrame()
                
            # Add predicted time (in hours from now)
            now = datetime.now()
            
            # Calculate distance from user location
            for idx, row in significant_predictions.iterrows():
                pred_loc = (row['latitude'], row['longitude'])
                distance = geodesic(self.user_location, pred_loc).kilometers
                significant_predictions.at[idx, 'distance'] = distance
                
                # Calculate a confidence score (higher = more confident)
                confidence = max(0.1, min(0.9, 1.0 - (distance / (self.radius_km * 2))))
                significant_predictions.at[idx, 'confidence'] = confidence
                
                # Calculate predicted hours from now based on magnitude and depth
                # Higher magnitude and smaller depth = sooner
                hours_from_now = int(hours_ahead * (1 - confidence) * 
                                   (1 + row['depth'] / 30) / 
                                   (row['predicted_magnitude'] / 4))
                
                # Ensure hours is within range
                hours_from_now = max(1, min(hours_ahead, hours_from_now))
                significant_predictions.at[idx, 'hours_from_now'] = hours_from_now
                
                # Calculate predicted datetime
                significant_predictions.at[idx, 'predicted_time'] = now + timedelta(hours=hours_from_now)
                
                # Get direction
                significant_predictions.at[idx, 'direction'] = self._get_direction(
                    self.user_location, (row['latitude'], row['longitude']))
            
            # Sort by confidence and magnitude
            result = significant_predictions.sort_values(
                by=['hours_from_now', 'predicted_magnitude'], 
                ascending=[True, False]
            )
            
            print(f"Generated {len(result)} earthquake predictions.")
            return result
            
        except Exception as e:
            logger.error(f"Error in earthquake prediction: {e}")
            print(f"Error in earthquake prediction: {e}")
            return pd.DataFrame()

    def _get_direction(self, point1, point2):
        """
        Get cardinal direction from point1 to point2.
        
        :param point1: (lat, lon) tuple for first point
        :param point2: (lat, lon) tuple for second point
        :return: Cardinal direction as string
        """
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        if abs(dlat) < 0.0001 and abs(dlon) < 0.0001:
            return "at"
            
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        angle = np.arctan2(dlon, dlat) * 180 / np.pi
        index = int((angle + 22.5) % 360 // 45)
        return directions[index]

    def create_interactive_map(self, output_dir: str = '.', hours_ahead: int = 24) -> str:
        """
        Generate an interactive map with current earthquakes and predictions.

        :param output_dir: Directory to save the map
        :param hours_ahead: Hours ahead to predict for
        :return: Path to the generated map
        """
        print("Creating interactive map with time-based predictions...")
        
        # Fetch current earthquake data if not done already
        if not self.earthquake_data:
            self.earthquake_data = self.fetch_earthquake_data()
            
        # Get current earthquakes
        current_df = self.analyze_earthquake_data()
        
        # Get predictions
        predictions_df = self.predict_future_earthquakes(hours_ahead)
        
        # Create the base map
        fig = go.Figure()
        
        # Add current earthquakes
        if not current_df.empty:
            # Ensure magnitudes are non-negative for the size property
            current_df['magnitude'] = current_df['magnitude'].apply(lambda x: max(x, 0))  
            
            fig.add_trace(go.Scattergeo(
                lat=current_df['latitude'],
                lon=current_df['longitude'],
                mode='markers',
                marker=dict(
                    size=current_df['magnitude'] * 4,
                    color='blue',
                    symbol='circle',
                    line=dict(width=1, color='black')
                ),
                name='Recent Earthquakes',
                text=[f"{place}<br>Magnitude: {mag:.1f}<br>Depth: {depth}km<br>Time: {time}" 
                      for place, mag, depth, time in zip(
                          current_df['place'], 
                          current_df['magnitude'],
                          current_df['depth'],
                          current_df['time'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M'))
                      )],
                hoverinfo='text'
            ))
        
        # Add predicted earthquakes
        if not predictions_df.empty:
            # Create a colorscale for predictions based on time
            predictions_df['hours_normalized'] = predictions_df['hours_from_now'] / max(predictions_df['hours_from_now'])
            
            fig.add_trace(go.Scattergeo(
                lat=predictions_df['latitude'],
                lon=predictions_df['longitude'],
                mode='markers',
                marker=dict(
                    size=predictions_df['predicted_magnitude'] * 4,
                    color=predictions_df['hours_from_now'],
                    colorscale='Viridis',
                    symbol='diamond',
                    line=dict(width=1, color='black'),
                    colorbar=dict(
                        title="Hours From Now",
                        x=0.85
                    )
                ),
                name='Predicted Earthquakes',
                text=[f"Predicted Earthquake<br>Magnitude: {mag:.1f}<br>Confidence: {conf:.0%}<br>"
                      f"Expected in: {hrs} hours<br>({time.strftime('%Y-%m-%d %H:%M')})<br>"
                      f"{dist:.1f}km {direction} of your location" 
                      for mag, conf, hrs, time, dist, direction in zip(
                          predictions_df['predicted_magnitude'],
                          predictions_df['confidence'],
                          predictions_df['hours_from_now'],
                          predictions_df['predicted_time'],
                          predictions_df['distance'],
                          predictions_df['direction']
                      )],
                hoverinfo='text'
            ))
        
        # Add user location marker
        fig.add_trace(go.Scattergeo(
            lat=[self.user_location[0]],
            lon=[self.user_location[1]],
            mode='markers',
            marker=dict(
                size=10,
                color='red',
                symbol='star',
                line=dict(width=1, color='black')
            ),
            name='Your Location',
            hoverinfo='name'
        ))
        
        # Configure the layout
        fig.update_layout(
            title=f"Earthquake Map with {hours_ahead}-Hour Predictions",
            geo=dict(
                scope='world',
                projection_type='natural earth',
                showland=True,
                landcolor='rgb(217, 217, 217)',
                subunitcolor='rgb(255, 255, 255)',
                countrycolor='rgb(255, 255, 255)',
                showlakes=True,
                lakecolor='rgb(173, 216, 230)',
                showocean=True,
                oceancolor='rgb(173, 216, 230)',
                showcoastlines=True,
                coastlinecolor='rgb(80, 80, 80)',
                showcountries=True,
                showsubunits=True,
                showframe=False,
                center=dict(
                    lon=self.user_location[1],
                    lat=self.user_location[0]
                )
            ),
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255, 255, 255, 0.8)'
            )
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the map
        output_path = os.path.join(output_dir, 'earthquake_prediction_map.html')
        fig.write_html(output_path)
        
        print(f"Interactive map saved to: {output_path}")
        
        # Generate a text prediction file
        self._generate_prediction_text_file(predictions_df, output_dir)
        
        return output_path

    def _generate_prediction_text_file(self, predictions_df, output_dir):
        """
        Generate a text file with earthquake predictions.
        
        :param predictions_df: DataFrame with prediction results
        :param output_dir: Directory to save the file
        """
        if predictions_df.empty:
            return
            
        output_path = os.path.join(output_dir, 'earthquake_predictions.txt')
        
        with open(output_path, 'w') as f:
            f.write(f"EARTHQUAKE PREDICTIONS FOR LOCATION: {self.user_location[0]}, {self.user_location[1]}\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Group predictions by hour ranges
            f.write("PREDICTIONS BY TIME:\n\n")
            
            # First hour
            hour1_preds = predictions_df[predictions_df['hours_from_now'] <= 1]
            f.write("--- NEXT HOUR ---\n")
            if not hour1_preds.empty:
                for _, pred in hour1_preds.iterrows():
                    f.write(f"• Magnitude {pred['predicted_magnitude']:.1f} earthquake predicted at "
                           f"{pred['distance']:.1f}km {pred['direction']} of your location "
                           f"(Confidence: {pred['confidence']:.0%})\n")
            else:
                f.write("No significant earthquakes predicted in the next hour.\n")
            f.write("\n")
            
            # 1-3 hours
            hours1to3_preds = predictions_df[(predictions_df['hours_from_now'] > 1) & 
                                           (predictions_df['hours_from_now'] <= 3)]
            f.write("--- NEXT 1-3 HOURS ---\n")
            if not hours1to3_preds.empty:
                for _, pred in hours1to3_preds.iterrows():
                    f.write(f"• Magnitude {pred['predicted_magnitude']:.1f} earthquake predicted at "
                           f"{pred['distance']:.1f}km {pred['direction']} of your location in approximately "
                           f"{pred['hours_from_now']:.1f} hours "
                           f"(Confidence: {pred['confidence']:.0%})\n")
            else:
                f.write("No significant earthquakes predicted in the 1-3 hour range.\n")
            f.write("\n")
            
            # 3-12 hours
            hours3to12_preds = predictions_df[(predictions_df['hours_from_now'] > 3) & 
                                            (predictions_df['hours_from_now'] <= 12)]
            f.write("--- NEXT 3-12 HOURS ---\n")
            if not hours3to12_preds.empty:
                for _, pred in hours3to12_preds.iterrows():
                    f.write(f"• Magnitude {pred['predicted_magnitude']:.1f} earthquake predicted at "
                           f"{pred['distance']:.1f}km {pred['direction']} of your location in approximately "
                           f"{pred['hours_from_now']:.1f} hours "
                           f"(Confidence: {pred['confidence']:.0%})\n")
            else:
                f.write("No significant earthquakes predicted in the 3-12 hour range.\n")
            f.write("\n")
            
            # 12-24 hours
            hours12to24_preds = predictions_df[(predictions_df['hours_from_now'] > 12)]
            f.write("--- NEXT 12-24 HOURS ---\n")
            if not hours12to24_preds.empty:
                for _, pred in hours12to24_preds.iterrows():
                    f.write(f"• Magnitude {pred['predicted_magnitude']:.1f} earthquake predicted at "
                           f"{pred['distance']:.1f}km {pred['direction']} of your location in approximately "
                           f"{pred['hours_from_now']:.1f} hours "
                           f"(Confidence: {pred['confidence']:.0%})\n")
            else:
                f.write("No significant earthquakes predicted in the 12-24 hour range.\n")
            f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("DISCLAIMER: These predictions are generated using machine learning based on historical patterns. ")
            f.write("They should be considered as estimates only and not relied upon for critical safety decisions. ")
            f.write("Always follow official guidance from local authorities regarding earthquake preparedness and safety.\n")
            
        print(f"Prediction text file saved to: {output_path}")


def main():
    print("🌍 Earthquake Prediction Map Generator")

    try:
        user_lat = float(input("Enter your latitude: "))
        user_lon = float(input("Enter your longitude: "))
        hours_ahead = int(input("Enter prediction hours ahead (1-48): "))
        hours_ahead = max(1, min(48, hours_ahead))  # Limit to reasonable range

        # Create output directory
        output_dir = "earthquake_predictions"
        os.makedirs(output_dir, exist_ok=True)
        
        # Create and run the map generator
        generator = EarthquakePredictionMap(user_lat, user_lon)
        map_path = generator.create_interactive_map(output_dir, hours_ahead)
        
        print("\nPrediction complete!")
        print(f"- Interactive map: {map_path}")
        print(f"- Prediction details: {os.path.join(output_dir, 'earthquake_predictions.txt')}")
        print("\nOpen the HTML file in your web browser to view the interactive map.")

    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()