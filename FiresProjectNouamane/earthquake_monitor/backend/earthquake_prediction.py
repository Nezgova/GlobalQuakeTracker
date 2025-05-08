"""
Earthquake prediction module using OpenQuake and statistical methods
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math
from scipy import stats
import random
from openquake.hazardlib import geo, const, mfd, source
from openquake.hazardlib.source import AreaSource, PointSource
from openquake.hazardlib.geo import Point, Polygon, NodalPlane
from openquake.hazardlib.sourceconverter import SourceConverter

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371  # Earth's radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat/2) * math.sin(dLat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon/2) * math.sin(dLon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

def calculate_temporal_patterns(earthquakes):
    """Analyze temporal patterns in earthquake data"""
    # Convert to pandas DataFrame for easier analysis
    if not earthquakes:
        return {"pattern": "insufficient_data", "periodicity": 0}
    
    df = pd.DataFrame([{
        'time': eq['properties']['time'],
        'timestamp': datetime.fromtimestamp(eq['properties']['time']/1000),
        'magnitude': eq['properties']['mag']
    } for eq in earthquakes if 'properties' in eq and 'time' in eq['properties']])
    
    if df.empty or len(df) < 5:
        return {"pattern": "insufficient_data", "periodicity": 0}
    
    # Sort by time
    df = df.sort_values('timestamp')
    
    # Calculate time differences between consecutive events
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / (24 * 3600)  # in days
    
    # Remove NaN (first row)
    df = df.dropna()
    
    if len(df) < 5:
        return {"pattern": "insufficient_data", "periodicity": 0}
    
    # Check for clustering
    time_diffs = df['time_diff'].values
    mean_diff = np.mean(time_diffs)
    std_diff = np.std(time_diffs)
    cv = std_diff / mean_diff if mean_diff > 0 else 0
    
    # Detect pattern
    if cv > 2.0:
        pattern = "clustered"
        # Check for potential periodicity
        try:
            # Simple FFT to check for periodicity
            from scipy import signal
            f, Pxx = signal.periodogram(time_diffs)
            max_idx = np.argmax(Pxx)
            peak_period = 1/f[max_idx] if f[max_idx] > 0 else 0
            periodicity = peak_period if peak_period < 365 else 0  # Cap at 1 year
        except:
            periodicity = 0
    elif cv < 0.3:
        pattern = "regular"
        periodicity = mean_diff
    else:
        pattern = "random"
        periodicity = 0
        
    return {
        "pattern": pattern,
        "periodicity": periodicity,
        "cv": cv,
        "mean_interval": mean_diff
    }
    
def calculate_magnitude_distribution(earthquakes):
    """Calculate Gutenberg-Richter relationship for magnitude distribution"""
    if not earthquakes:
        return {"a_value": 0, "b_value": 0}
        
    # Extract magnitudes
    magnitudes = [eq['properties']['mag'] for eq in earthquakes 
                  if 'properties' in eq and 'mag' in eq['properties']]
    
    if not magnitudes or len(magnitudes) < 5:
        return {"a_value": 0, "b_value": 0}
    
    # Create histogram
    hist, bin_edges = np.histogram(magnitudes, bins=10)
    
    # Calculate cumulative number (N) of earthquakes above magnitude M
    N = np.array([sum(m >= edge for m in magnitudes) for edge in bin_edges[:-1]])
    M = bin_edges[:-1]
    
    # Filter out zeros for log calculation
    valid_idx = N > 0
    if sum(valid_idx) < 3:
        return {"a_value": 0, "b_value": 0}
        
    N_valid = N[valid_idx]
    M_valid = M[valid_idx]
    
    # Log10(N) = a - bM
    log_N = np.log10(N_valid)
    
    try:
        # Linear regression to find a and b values
        slope, intercept, r_value, p_value, std_err = stats.linregress(M_valid, log_N)
        
        # In G-R relationship, slope is -b
        b_value = -slope
        a_value = intercept
        
        return {
            "a_value": a_value,
            "b_value": b_value,
            "r_squared": r_value**2
        }
    except:
        return {"a_value": 0, "b_value": 0}

def predict_future_earthquakes(lat, lon, earthquakes, time_horizon=30, intensity_threshold=4.0):
    """
    Predict future earthquakes using historical data and statistical methods
    
    Args:
        lat (float): Latitude of the target location
        lon (float): Longitude of the target location
        earthquakes (list): List of earthquake data
        time_horizon (int): Time horizon for prediction in days
        intensity_threshold (float): Minimum magnitude to consider
        
    Returns:
        dict: Prediction results
    """
    try:
        # Validate input data format
        if not isinstance(earthquakes, (list, tuple)):
            return {
                "status": "error",
                "message": "Earthquake data must be a list",
                "predictions": []
            }

        nearby_earthquakes = []
        for eq in earthquakes:
            try:
                # Safely access earthquake properties
                if not isinstance(eq, dict):
                    continue
                    
                # Check if geometry exists and has coordinates
                if 'geometry' not in eq or not isinstance(eq['geometry'], dict):
                    continue
                    
                coordinates = eq['geometry'].get('coordinates')
                if not coordinates or len(coordinates) < 2:
                    continue
                    
                eq_lon, eq_lat = coordinates[0], coordinates[1]
                
                # Check if properties exist and have required fields
                if 'properties' not in eq or not isinstance(eq['properties'], dict):
                    continue
                    
                if 'time' not in eq['properties'] or 'mag' not in eq['properties']:
                    continue
                    
                # Calculate distance
                distance = calculate_distance(lat, lon, eq_lat, eq_lon)
                if distance <= 500:  # 500km radius
                    eq['distance'] = distance
                    nearby_earthquakes.append(eq)
                    
            except (KeyError, TypeError, ValueError) as e:
                print(f"Skipping invalid earthquake entry: {str(e)}")
                continue
    
        # Rest of your existing function...
        # [Keep all the remaining code the same]
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate prediction: {str(e)}",
            "predictions": []
        }
    """
    Predict future earthquakes using historical data and statistical methods
    
    Args:
        lat (float): Latitude of the target location
        lon (float): Longitude of the target location
        earthquakes (list): List of earthquake data
        time_horizon (int): Time horizon for prediction in days
        intensity_threshold (float): Minimum magnitude to consider
        
    Returns:
        dict: Prediction results
    """
    # Filter earthquakes within 500km radius
    nearby_earthquakes = []
    for eq in earthquakes:
        eq_lat = eq['geometry']['coordinates'][1]
        eq_lon = eq['geometry']['coordinates'][0]
        distance = calculate_distance(lat, lon, eq_lat, eq_lon)
        if distance <= 500:  # 500km radius
            eq['distance'] = distance
            nearby_earthquakes.append(eq)
    
    if len(nearby_earthquakes) < 10:
        return {
            "status": "insufficient_data",
            "message": "Not enough historical earthquake data for a reliable prediction.",
            "predictions": []
        }
    
    # Analyze temporal patterns
    temporal_patterns = calculate_temporal_patterns(nearby_earthquakes)
    
    # Analyze magnitude distribution
    magnitude_dist = calculate_magnitude_distribution(nearby_earthquakes)
    
    # Generate prediction
    predictions = []
    current_time = datetime.now()
    
    # Different prediction logic based on pattern
    if temporal_patterns["pattern"] == "clustered":
        # For clustered pattern, predict aftershock sequence
        recent_events = sorted(nearby_earthquakes, 
                              key=lambda x: x['properties']['time'], 
                              reverse=True)[:5]
        
        if recent_events:
            # Omori's law for aftershock decay
            for i in range(1, 6):  # Predict up to 5 potential aftershocks
                days_offset = i * (temporal_patterns["mean_interval"] or 7)
                if days_offset > time_horizon:
                    break
                    
                # Estimate magnitude (typically decreasing)
                main_mag = recent_events[0]['properties']['mag']
                predicted_mag = max(main_mag - 0.5 * math.log10(i + 1), intensity_threshold)
                
                if predicted_mag >= intensity_threshold:
                    predictions.append({
                        "predicted_time": (current_time + timedelta(days=days_offset)).isoformat(),
                        "days_from_now": days_offset,
                        "estimated_magnitude": round(predicted_mag, 1),
                        "probability": max(0.9 - (i * 0.15), 0.2),
                        "prediction_type": "aftershock"
                    })
                    
    elif temporal_patterns["pattern"] == "regular" and temporal_patterns["periodicity"] > 0:
        # For regular pattern, predict based on periodicity
        for i in range(1, int(time_horizon / temporal_patterns["periodicity"]) + 1):
            days_offset = i * temporal_patterns["periodicity"]
            if days_offset <= time_horizon:
                # Use G-R relationship for magnitude estimation
                if magnitude_dist["b_value"] > 0:
                    # Calculate magnitude with some randomness
                    rand_factor = random.uniform(0.8, 1.2)
                    predicted_mag = intensity_threshold + (
                        math.log10(random.random()) / 
                        (-magnitude_dist["b_value"] * rand_factor)
                    )
                    predicted_mag = min(max(predicted_mag, intensity_threshold), 7.5)  # Cap between threshold and 7.5
                else:
                    # Fallback if no good G-R relationship
                    avg_mag = np.mean([eq['properties']['mag'] for eq in nearby_earthquakes])
                    predicted_mag = max(avg_mag * random.uniform(0.9, 1.1), intensity_threshold)
                
                predictions.append({
                    "predicted_time": (current_time + timedelta(days=days_offset)).isoformat(),
                    "days_from_now": days_offset,
                    "estimated_magnitude": round(predicted_mag, 1),
                    "probability": 0.7 - (i * 0.05),  # Decreasing probability with time
                    "prediction_type": "periodic"
                })
    else:
        # For random pattern, use Poisson process
        # Calculate average number of events per time_horizon
        total_time_span = max(eq['properties']['time'] for eq in nearby_earthquakes) - \
                         min(eq['properties']['time'] for eq in nearby_earthquakes)
        total_time_span_days = total_time_span / (1000 * 86400)  # Convert ms to days
        
        if total_time_span_days > 0:
            events_above_threshold = sum(1 for eq in nearby_earthquakes 
                                       if eq['properties']['mag'] >= intensity_threshold)
            
            rate = events_above_threshold / total_time_span_days
            expected_events = rate * time_horizon
            
            # Simulate Poisson process
            if expected_events > 0:
                # Number of events in the period
                num_events = np.random.poisson(expected_events)
                
                # Random times for the events
                event_times = sorted(np.random.uniform(0, time_horizon, num_events))
                
                for i, days_offset in enumerate(event_times):
                    # Generate magnitude using G-R relationship
                    if magnitude_dist["b_value"] > 0:
                        u = random.random()
                        # Use inverse transform sampling with G-R CDF
                        predicted_mag = intensity_threshold + math.log10(u) / (-magnitude_dist["b_value"])
                        predicted_mag = min(max(predicted_mag, intensity_threshold), 7.5)
                    else:
                        # Fallback magnitude estimate
                        avg_mag = np.mean([eq['properties']['mag'] for eq in nearby_earthquakes])
                        predicted_mag = max(avg_mag * random.uniform(0.9, 1.1), intensity_threshold)
                    
                    predictions.append({
                        "predicted_time": (current_time + timedelta(days=days_offset)).isoformat(),
                        "days_from_now": round(days_offset, 1),
                        "estimated_magnitude": round(predicted_mag, 1),
                        "probability": 0.5 - (i * 0.02),  # Decreasing probability with index
                        "prediction_type": "stochastic"
                    })
    
    # Calculate overall probability
    recent_significant = sum(1 for eq in nearby_earthquakes 
                           if eq['properties']['mag'] >= intensity_threshold and
                              (datetime.now() - datetime.fromtimestamp(eq['properties']['time']/1000)).days <= 30)
    
    base_probability = min(0.1 + (recent_significant * 0.05), 0.9)
    
    # Create response
    return {
        "status": "success",
        "location": {
            "latitude": lat,
            "longitude": lon
        },
        "time_horizon_days": time_horizon,
        "intensity_threshold": intensity_threshold,
        "prediction_timestamp": datetime.now().isoformat(),
        "analysis": {
            "pattern_type": temporal_patterns["pattern"],
            "periodicity_days": round(temporal_patterns["periodicity"], 2) if temporal_patterns["periodicity"] else 0,
            "historical_events_count": len(nearby_earthquakes),
            "gutenberg_richter": {
                "a_value": round(magnitude_dist["a_value"], 3) if magnitude_dist["a_value"] else 0,
                "b_value": round(magnitude_dist["b_value"], 3) if magnitude_dist["b_value"] else 0
            }
        },
        "general_probability": base_probability,
        "predictions": sorted(predictions, key=lambda x: x["days_from_now"])
    }