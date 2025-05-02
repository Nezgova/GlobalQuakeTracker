import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from math import radians, cos, sin, asin, sqrt

# USGS Earthquake API endpoint
USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def fetch_earthquake_data(days=30):
    """
    Fetch earthquake data from USGS API for the specified number of days.
    
    Args:
        days (int): Number of days to look back (default: 30)
        
    Returns:
        dict: JSON response from USGS API
    """
    # Calculate start date
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for USGS API
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Set up parameters for API request
    params = {
        'format': 'geojson',
        'starttime': start_str,
        'endtime': end_str,
        'minmagnitude': 2.5,  # Get all earthquakes above 2.5 for more complete dataset
        'orderby': 'time'
    }
    
    try:
        response = requests.get(USGS_API_URL, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching earthquake data: {e}")
        return None

def haversine_distance(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    
    Returns:
        float: Distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def process_earthquake_data(raw_data, days_ago=7, min_magnitude=4.0):
    """
    Process and filter raw earthquake data.
    
    Args:
        raw_data (dict): Raw GeoJSON data from USGS API
        days_ago (int): Filter to earthquakes within this many days
        min_magnitude (float): Minimum earthquake magnitude to include
        
    Returns:
        dict: Filtered and processed earthquake data
    """
    if not raw_data or 'features' not in raw_data:
        return {"features": []}
    
    # Convert to more workable format
    features = raw_data['features']
    
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days_ago)
    
    # Filter earthquakes by date and magnitude
    filtered_features = []
    for feature in features:
        properties = feature['properties']
        geometry = feature['geometry']
        
        # Get timestamp and convert to datetime
        timestamp = properties.get('time', 0) / 1000  # Convert from milliseconds to seconds
        event_date = datetime.fromtimestamp(timestamp)
        
        # Check if event is within the time window and meets magnitude threshold
        if event_date >= cutoff_date and properties.get('mag', 0) >= min_magnitude:
            # Add additional processed properties
            properties['date_string'] = event_date.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Calculate intensity metrics
            magnitude = properties.get('mag', 0)
            depth = geometry['coordinates'][2]  # Z coordinate is depth in km
            
            # Simplified intensity calculation based on magnitude and depth
            # This is a basic approximation - real intensity calculations are more complex
            intensity = calculate_intensity(magnitude, depth)
            properties['estimated_intensity'] = intensity
            
            filtered_features.append(feature)
    
    # Sort by magnitude (descending)
    filtered_features.sort(key=lambda x: x['properties'].get('mag', 0), reverse=True)
    
    return {
        "type": "FeatureCollection",
        "features": filtered_features,
        "metadata": {
            "count": len(filtered_features),
            "generated": datetime.utcnow().isoformat(),
            "filter": {
                "days": days_ago,
                "min_magnitude": min_magnitude
            }
        }
    }

def calculate_intensity(magnitude, depth):
    """
    Calculate estimated intensity using a simplified formula.
    
    Args:
        magnitude (float): Earthquake magnitude
        depth (float): Depth in kilometers
        
    Returns:
        float: Estimated Modified Mercalli Intensity (MMI)
    """
    # This is a simplified approximation of MMI, not for scientific use
    # Real intensity calculations consider many more factors
    # Base intensity from magnitude (using simplified relationship)
    base_intensity = 1.5 * magnitude - 1.0
    
    # Depth adjustment (deeper earthquakes have less surface intensity)
    depth_factor = max(0, 1 - (depth / 100))
    
    # Combine factors (clamp between 1-10 for MMI scale)
    intensity = base_intensity * depth_factor
    return min(max(round(intensity * 10) / 10, 1), 10)

def filter_by_distance(earthquakes, center_lat, center_lon, radius_km):
    """
    Filter earthquakes by distance from a point.
    
    Args:
        earthquakes (dict): Processed earthquake GeoJSON
        center_lat (float): Latitude of center point
        center_lon (float): Longitude of center point
        radius_km (float): Radius in kilometers
        
    Returns:
        dict: Filtered earthquake data with distance added
    """
    # Make a copy to avoid modifying the original
    result = {
        "type": "FeatureCollection",
        "features": [],
        "metadata": earthquakes.get("metadata", {})
    }
    
    for feature in earthquakes["features"]:
        coords = feature["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]
        
        # Calculate distance
        distance = haversine_distance(center_lon, center_lat, lon, lat)
        
        # Add distance to properties
        feature["properties"]["distance_km"] = round(distance, 1)
        
        # Include if within radius
        if distance <= radius_km:
            result["features"].append(feature)
    
    # Update metadata
    result["metadata"]["filter"] = {
        **result["metadata"].get("filter", {}),
        "center": [center_lat, center_lon],
        "radius_km": radius_km,
        "count": len(result["features"])
    }
    
    return result