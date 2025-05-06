"""
Earthquake prediction module using OpenQuake and statistical methods
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math
from scipy import stats
import random
import traceback

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
    
    try:
        # Create a list for valid earthquake data points
        valid_data = []
        for eq in earthquakes:
            try:
                # Safely access properties
                if isinstance(eq, dict) and 'properties' in eq:
                    props = eq['properties']
                    if 'time' in props and 'mag' in props:
                        # Convert time to datetime
                        if isinstance(props['time'], (int, float)):
                            timestamp = datetime.fromtimestamp(props['time']/1000)
                            valid_data.append({
                                'time': props['time'],
                                'timestamp': timestamp,
                                'magnitude': props['mag']
                            })
            except Exception as e:
                print(f"Skipping invalid earthquake entry in temporal pattern analysis: {str(e)}")
                continue
                
        df = pd.DataFrame(valid_data)
        
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
    except Exception as e:
        print(f"Error in calculate_temporal_patterns: {str(e)}")
        traceback.print_exc()
        return {"pattern": "error", "periodicity": 0, "error": str(e)}
    
def calculate_magnitude_distribution(earthquakes):
    """Calculate Gutenberg-Richter relationship for magnitude distribution"""
    if not earthquakes:
        return {"a_value": 0, "b_value": 0}
        
    try:
        # Extract magnitudes
        magnitudes = []
        for eq in earthquakes:
            try:
                if isinstance(eq, dict) and 'properties' in eq:
                    props = eq['properties']
                    if 'mag' in props and props['mag'] is not None:
                        magnitudes.append(props['mag'])
            except Exception as e:
                print(f"Skipping invalid earthquake entry in magnitude distribution: {str(e)}")
                continue
        
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
        except Exception as e:
            print(f"Error in linregress: {str(e)}")
            return {"a_value": 0, "b_value": 0}
    except Exception as e:
        print(f"Error in calculate_magnitude_distribution: {str(e)}")
        traceback.print_exc()
        return {"a_value": 0, "b_value": 0, "error": str(e)}

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
        print(f"Starting prediction for location ({lat}, {lon}) with {len(earthquakes) if earthquakes else 0} earthquakes")
        
        # Validate input data format
        if not isinstance(earthquakes, list):
            return {
                "status": "error",
                "message": "Earthquake data must be a list",
                "predictions": []
            }

        # Filter earthquakes within 500km radius
        nearby_earthquakes = []
        for eq in earthquakes:
            try:
                # Verify we have a proper earthquake object
                if not isinstance(eq, dict):
                    continue
                
                # Get coordinates
                if 'geometry' not in eq or not isinstance(eq['geometry'], dict):
                    continue
                
                geometry = eq['geometry']
                if 'coordinates' not in geometry or not isinstance(geometry['coordinates'], list):
                    continue
                
                coords = geometry['coordinates']
                if len(coords) < 2:
                    continue
                
                # GeoJSON format has [longitude, latitude] order
                eq_lon, eq_lat = coords[0], coords[1]
                
                # Verify properties exist
                if 'properties' not in eq or not isinstance(eq['properties'], dict):
                    continue
                
                props = eq['properties']
                if 'time' not in props or 'mag' not in props:
                    continue
                
                # Calculate distance
                distance = calculate_distance(lat, lon, eq_lat, eq_lon)
                if distance <= 500:  # 500km radius
                    eq['distance'] = distance
                    nearby_earthquakes.append(eq)
            except Exception as e:
                print(f"Error processing earthquake entry: {str(e)}")
                continue
                
        print(f"Found {len(nearby_earthquakes)} nearby earthquakes within 500km")
        
        if len(nearby_earthquakes) < 10:
            return {
                "status": "insufficient_data",
                "message": "Not enough historical earthquake data for a reliable prediction.",
                "predictions": []
            }
        
        # Analyze temporal patterns
        temporal_patterns = calculate_temporal_patterns(nearby_earthquakes)
        print(f"Temporal patterns analysis: {temporal_patterns}")
        
        # Analyze magnitude distribution
        magnitude_dist = calculate_magnitude_distribution(nearby_earthquakes)
        print(f"Magnitude distribution analysis: {magnitude_dist}")
        
        # Generate prediction
        predictions = []
        current_time = datetime.now()
        
        # Different prediction logic based on pattern
        if temporal_patterns["pattern"] == "clustered":
            # For clustered pattern, predict aftershock sequence
            try:
                # Sort by time (most recent first)
                recent_events = sorted(
                    nearby_earthquakes, 
                    key=lambda x: x['properties']['time'] if isinstance(x['properties']['time'], (int, float)) else 0, 
                    reverse=True
                )[:5]
                
                if recent_events:
                    # Omori's law for aftershock decay
                    for i in range(1, 6):  # Predict up to 5 potential aftershocks
                        days_offset = i * (temporal_patterns.get("mean_interval", 0) or 7)
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
            except Exception as e:
                print(f"Error in clustered prediction: {str(e)}")
                traceback.print_exc()
                
        elif temporal_patterns["pattern"] == "regular" and temporal_patterns.get("periodicity", 0) > 0:
            # For regular pattern, predict based on periodicity
            try:
                periodicity = temporal_patterns.get("periodicity", 7)  # Default to weekly if missing
                for i in range(1, int(time_horizon / periodicity) + 1):
                    days_offset = i * periodicity
                    if days_offset <= time_horizon:
                        # Use G-R relationship for magnitude estimation
                        if magnitude_dist.get("b_value", 0) > 0:
                            # Calculate magnitude with some randomness
                            rand_factor = random.uniform(0.8, 1.2)
                            predicted_mag = intensity_threshold + (
                                math.log10(random.random()) / 
                                (-magnitude_dist["b_value"] * rand_factor)
                            )
                            predicted_mag = min(max(predicted_mag, intensity_threshold), 7.5)  # Cap between threshold and 7.5
                        else:
                            # Fallback if no good G-R relationship
                            mags = [eq['properties']['mag'] for eq in nearby_earthquakes 
                                   if isinstance(eq, dict) and 'properties' in eq and 'mag' in eq['properties']]
                            avg_mag = np.mean(mags) if mags else intensity_threshold
                            predicted_mag = max(avg_mag * random.uniform(0.9, 1.1), intensity_threshold)
                        
                        predictions.append({
                            "predicted_time": (current_time + timedelta(days=days_offset)).isoformat(),
                            "days_from_now": days_offset,
                            "estimated_magnitude": round(predicted_mag, 1),
                            "probability": 0.7 - (i * 0.05),  # Decreasing probability with time
                            "prediction_type": "periodic"
                        })
            except Exception as e:
                print(f"Error in regular pattern prediction: {str(e)}")
                traceback.print_exc()
                
        else:
            # For random pattern, use Poisson process
            try:
                # Calculate average number of events per time_horizon
                times = [eq['properties']['time'] for eq in nearby_earthquakes 
                         if isinstance(eq, dict) and 'properties' in eq and 'time' in eq['properties']]
                
                if times:
                    total_time_span = max(times) - min(times)
                    total_time_span_days = total_time_span / (1000 * 86400)  # Convert ms to days
                    
                    if total_time_span_days > 0:
                        events_above_threshold = sum(1 for eq in nearby_earthquakes 
                                                if isinstance(eq, dict) and 'properties' in eq and
                                                'mag' in eq['properties'] and
                                                eq['properties']['mag'] >= intensity_threshold)
                        
                        rate = events_above_threshold / total_time_span_days
                        expected_events = rate * time_horizon
                        
                        # Simulate Poisson process
                        if expected_events > 0:
                            # Number of events in the period
                            num_events = np.random.poisson(expected_events)
                            
                            # Random times for the events
                            event_times = sorted(np.random.uniform(0, time_horizon, num_events))
                            
                            for i, days_offset in enumerate(event_times):
                                # Generate magnitude based on G-R relationship if available
                                if magnitude_dist.get("b_value", 0) > 0:
                                    rand_factor = random.uniform(0.8, 1.2)
                                    predicted_mag = intensity_threshold + (
                                        math.log10(random.random()) / 
                                        (-magnitude_dist["b_value"] * rand_factor)
                                    )
                                    predicted_mag = min(max(predicted_mag, intensity_threshold), 7.0)
                                else:
                                    # Fallback to historical average with randomness
                                    mags = [eq['properties']['mag'] for eq in nearby_earthquakes 
                                           if isinstance(eq, dict) and 'properties' in eq and 'mag' in eq['properties']]
                                    avg_mag = np.mean(mags) if mags else intensity_threshold
                                    predicted_mag = max(avg_mag * random.uniform(0.9, 1.1), intensity_threshold)
                                
                                predictions.append({
                                    "predicted_time": (current_time + timedelta(days=days_offset)).isoformat(),
                                    "days_from_now": days_offset,
                                    "estimated_magnitude": round(predicted_mag, 1),
                                    "probability": 0.5 - (i * 0.02),  # Decreasing probability based on order
                                    "prediction_type": "stochastic"
                                })
            except Exception as e:
                print(f"Error in random pattern prediction: {str(e)}")
                traceback.print_exc()
        
        # If no predictions were made, add a low-probability generic prediction
        if not predictions and nearby_earthquakes:
            try:
                # Use average magnitude and time interval
                mags = [eq['properties']['mag'] for eq in nearby_earthquakes 
                       if isinstance(eq, dict) and 'properties' in eq and 'mag' in eq['properties']]
                avg_mag = np.mean(mags) if mags else intensity_threshold
                
                # Add one generic prediction
                predictions.append({
                    "predicted_time": (current_time + timedelta(days=time_horizon/2)).isoformat(),
                    "days_from_now": time_horizon/2,
                    "estimated_magnitude": round(max(avg_mag, intensity_threshold), 1),
                    "probability": 0.3,
                    "prediction_type": "general"
                })
            except Exception as e:
                print(f"Error creating generic prediction: {str(e)}")
        
        # Sort predictions by time
        predictions.sort(key=lambda x: x["days_from_now"])
        
        # Add confidence level based on data quality
        confidence_level = "low"
        if len(nearby_earthquakes) > 50:
            if magnitude_dist.get("r_squared", 0) > 0.8:
                confidence_level = "high"
            else:
                confidence_level = "medium"
        elif len(nearby_earthquakes) > 20:
            confidence_level = "medium"
            
        # Format the response to include all required data for front end display
        return {
            "status": "success",
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "analysis_parameters": {
                "time_horizon_days": time_horizon,
                "intensity_threshold": intensity_threshold,
                "data_points_analyzed": len(nearby_earthquakes),
                "confidence_level": confidence_level
            },
            "temporal_pattern": temporal_patterns,
            "magnitude_distribution": magnitude_dist,
            "predictions": predictions
        }
    except Exception as e:
        print(f"Critical error in predict_future_earthquakes: {str(e)}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Prediction failed: {str(e)}",
            "predictions": []
        }