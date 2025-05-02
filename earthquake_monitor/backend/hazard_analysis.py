import numpy as np
from math import radians, cos, sin, asin, sqrt
import pandas as pd
from datetime import datetime, timedelta
from data_processor import filter_by_distance, haversine_distance

# Note: This is a mock implementation of hazard analysis
# For a real application, consider using established libraries like OpenQuake

def perform_hazard_analysis(earthquakes, center_lat, center_lon, radius_km=300):
    """
    Perform a simplified seismic hazard analysis for a given location.
    
    Args:
        earthquakes (dict): Processed earthquake GeoJSON data
        center_lat (float): Latitude of center point
        center_lon (float): Longitude of center point  
        radius_km (float): Radius to consider for analysis (default: 300km)
        
    Returns:
        dict: Analysis results
    """
    # Filter earthquakes by distance
    nearby_earthquakes = filter_by_distance(earthquakes, center_lat, center_lon, radius_km)
    
    # If no earthquakes in range, return empty analysis
    if len(nearby_earthquakes["features"]) == 0:
        return {
            "status": "no_data",
            "location": {
                "latitude": center_lat,
                "longitude": center_lon,
                "radius_km": radius_km
            },
            "hazard_level": "unknown",
            "max_magnitude": None,
            "earthquake_count": 0,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    # Extract key metrics
    magnitudes = [eq["properties"]["mag"] for eq in nearby_earthquakes["features"] if "mag" in eq["properties"]]
    depths = [eq["geometry"]["coordinates"][2] for eq in nearby_earthquakes["features"]]
    distances = [eq["properties"].get("distance_km", 0) for eq in nearby_earthquakes["features"]]
    times = [eq["properties"]["time"] for eq in nearby_earthquakes["features"] if "time" in eq["properties"]]
    
    # Convert times to datetime objects
    datetimes = [datetime.fromtimestamp(t/1000) for t in times]  # USGS time is in milliseconds
    
    # Calculate time since most recent significant earthquake
    if datetimes:
        most_recent = max(datetimes)
        days_since_recent = (datetime.utcnow() - most_recent).total_seconds() / (24 * 3600)
    else:
        days_since_recent = None
    
    # Basic statistics
    earthquake_count = len(nearby_earthquakes["features"])
    max_magnitude = max(magnitudes) if magnitudes else 0
    avg_magnitude = sum(magnitudes) / len(magnitudes) if magnitudes else 0
    avg_depth = sum(depths) / len(depths) if depths else 0
    
    # Calculate recurrence intervals
    # (This is a simplified approach - real analysis would be more complex)
    if len(datetimes) >= 2:
        # Sort by time
        sorted_times = sorted(datetimes)
        
        # Calculate intervals between events in days
        intervals = [(sorted_times[i] - sorted_times[i-1]).total_seconds() / (24 * 3600) 
                      for i in range(1, len(sorted_times))]
        
        avg_interval = sum(intervals) / len(intervals) if intervals else None
        min_interval = min(intervals) if intervals else None
        max_interval = max(intervals) if intervals else None
    else:
        avg_interval = None
        min_interval = None
        max_interval = None
    
    # Calculate earthquake density (events per 10,000 sq km per year)
    area = np.pi * (radius_km ** 2)  # Area in sq km
    time_span = 7  # Default 7 days of data
    density = (earthquake_count / (area / 10000)) * (365 / time_span)
    
    # Calculate magnitude-frequency distribution (b-value)
    # This is a simplified Gutenberg-Richter calculation
    b_value = calculate_b_value(magnitudes) if len(magnitudes) >= 5 else None
    
    # Calculate peak ground acceleration (PGA) estimate
    # This is highly simplified - real PGA calculations require more sophisticated models
    pga_estimate = estimate_pga(max_magnitude, min(distances) if distances else 0)
    
    # Determine hazard level based on various factors
    hazard_level = calculate_hazard_level(
        max_magnitude, 
        earthquake_count,
        avg_interval,
        days_since_recent,
        pga_estimate
    )
    
    # Return analysis results
    return {
        "status": "success",
        "location": {
            "latitude": center_lat,
            "longitude": center_lon,
            "radius_km": radius_km
        },
        "hazard_level": hazard_level,
        "hazard_score": calculate_hazard_score(
            max_magnitude, 
            earthquake_count,
            avg_interval,
            days_since_recent,
            pga_estimate
        ),
        "metrics": {
            "earthquake_count": earthquake_count,
            "max_magnitude": round(max_magnitude, 1) if max_magnitude else None,
            "avg_magnitude": round(avg_magnitude, 1) if avg_magnitude else None,
            "avg_depth_km": round(avg_depth, 1) if avg_depth else None,
            "earthquake_density": round(density, 2),
            "days_since_recent": round(days_since_recent, 1) if days_since_recent else None,
            "avg_interval_days": round(avg_interval, 1) if avg_interval else None,
            "min_interval_days": round(min_interval, 1) if min_interval else None,
            "b_value": round(b_value, 2) if b_value else None,
            "pga_estimate": round(pga_estimate, 3) if pga_estimate else None
        },
        "analysis_date": datetime.utcnow().isoformat(),
        "nearest_earthquakes": [
            {
                "id": eq["id"],
                "magnitude": eq["properties"]["mag"],
                "depth": eq["geometry"]["coordinates"][2],
                "distance": eq["properties"].get("distance_km", 0),
                "date": datetime.fromtimestamp(eq["properties"]["time"]/1000).isoformat(),
                "location": eq["properties"]["place"]
            }
            for eq in sorted(nearby_earthquakes["features"], 
                            key=lambda x: x["properties"].get("distance_km", float('inf')))[:5]
        ]
    }

def calculate_b_value(magnitudes):
    """
    Calculate the b-value from the Gutenberg-Richter relationship.
    
    Args:
        magnitudes (list): List of earthquake magnitudes
        
    Returns:
        float: Estimated b-value
    """
    if len(magnitudes) < 5:
        return None
        
    # Simple method using linear regression
    # Log(N) = a - b*M where N is number of earthquakes with magnitude >= M
    
    # Create bins of magnitude
    bins = np.arange(min(magnitudes), max(magnitudes) + 0.1, 0.1)
    
    # Count earthquakes in each bin
    counts = []
    for m in bins:
        count = sum(1 for mag in magnitudes if mag >= m)
        if count > 0:  # Avoid log(0)
            counts.append(np.log10(count))
        else:
            counts.append(0)
    
    # Simple linear regression
    if len(bins) > 1 and len(counts) > 1:
        slope, _ = np.polyfit(bins, counts, 1)
        return -slope  # b-value is negative of slope
    else:
        return None

def estimate_pga(magnitude, distance_km):
    """
    Estimate Peak Ground Acceleration (PGA) using a simplified attenuation relationship.
    
    Args:
        magnitude (float): Earthquake magnitude
        distance_km (float): Distance from epicenter in km
        
    Returns:
        float: Estimated PGA in g (gravity)
    """
    if distance_km < 1:
        distance_km = 1  # Avoid division by zero
        
    # Very simplified PGA calculation based on magnitude and distance
    # Real calculations would use proper ground motion prediction equations (GMPEs)
    # This is just for demonstration
    pga = 10**(0.67*magnitude - 1.7*np.log10(distance_km) - 1.6)
    
    return pga

def calculate_hazard_level(magnitude, count, interval, days_since_recent, pga):
    """
    Calculate a qualitative hazard level based on analysis metrics.
    
    Args:
        magnitude (float): Maximum earthquake magnitude
        count (int): Number of earthquakes
        interval (float): Average interval between earthquakes in days
        days_since_recent (float): Days since most recent earthquake
        pga (float): Estimated Peak Ground Acceleration
        
    Returns:
        str: Hazard level (low, moderate, high, very_high)
    """
    # Calculate hazard score (0-100)
    score = calculate_hazard_score(magnitude, count, interval, days_since_recent, pga)
    
    # Map score to hazard level
    if score < 25:
        return "low"
    elif score < 50:
        return "moderate"
    elif score < 75:
        return "high"
    else:
        return "very_high"

def calculate_hazard_score(magnitude, count, interval, days_since_recent, pga):
    """
    Calculate a hazard score (0-100) based on analysis metrics.
    
    Args:
        magnitude (float): Maximum earthquake magnitude
        count (int): Number of earthquakes
        interval (float): Average interval between earthquakes in days
        days_since_recent (float): Days since most recent earthquake
        pga (float): Estimated Peak Ground Acceleration
        
    Returns:
        float: Hazard score (0-100)
    """
    # Initialize base score
    score = 0
    
    # Factor 1: Magnitude contribution (0-40 points)
    if magnitude:
        # Each increment of 1 in magnitude represents ~32x energy
        # Mag 3 = ~0 points, Mag 5 = ~20 points, Mag 7 = ~40 points
        mag_score = (magnitude - 3) * 10 if magnitude > 3 else 0
        score += min(40, max(0, mag_score))
    
    # Factor 2: Activity rate contribution (0-20 points)
    if count:
        # More earthquakes = higher hazard
        count_score = min(20, count / 2)
        score += count_score
    
    # Factor 3: Recency contribution (0-20 points)
    if days_since_recent is not None:
        # More recent = higher hazard
        # <1 day = 20 points, 30+ days = 0 points
        recency_score = max(0, 20 - (days_since_recent / 1.5))
        score += recency_score
    
    # Factor 4: PGA contribution (0-20 points)
    if pga:
        # PGA < 0.01g = ~0 points, PGA > 0.5g = ~20 points
        pga_score = min(20, pga * 40)
        score += pga_score
    
    return round(score, 1)