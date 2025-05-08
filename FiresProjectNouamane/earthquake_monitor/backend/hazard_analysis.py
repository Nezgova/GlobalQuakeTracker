import os
import tempfile
import json
from openquake.hazardlib import geo, const, imt
from openquake.hazardlib.calc import hazard_curve, filters
from openquake.hazardlib.source import PointSource
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import math

# Current function from existing application, keep for compatibility
def perform_hazard_analysis(earthquakes, lat, lon, radius=300):
    """
    Perform hazard analysis on the given earthquakes around a location.
    This is the existing function used in your application.
    
    Args:
        earthquakes (dict): Dictionary containing earthquake data
        lat (float): Latitude of the point of interest
        lon (float): Longitude of the point of interest
        radius (float): Radius around the point in kilometers
        
    Returns:
        dict: Analysis results
    """
    # Extract features from earthquakes
    features = earthquakes.get('features', [])
    
    # Find earthquakes within radius
    nearby_quakes = []
    for quake in features:
        quake_coords = quake['geometry']['coordinates']
        quake_lon, quake_lat, quake_depth = quake_coords
        
        # Calculate distance (simplified haversine)
        distance = calculate_distance(lat, lon, quake_lat, quake_lon)
        
        if distance <= radius:
            # Add distance to quake properties
            quake_props = quake['properties'].copy()
            quake_props['distance'] = distance
            
            nearby_quakes.append({
                'geometry': quake['geometry'],
                'properties': quake_props,
                'id': quake['id'],
                'type': quake['type']
            })
    
    # Calculate statistics
    total_count = len(nearby_quakes)
    
    # Prepare magnitude bins
    mag_bins = {
        '0-2.9': 0,
        '3.0-3.9': 0,
        '4.0-4.9': 0,
        '5.0-5.9': 0,
        '6.0+': 0
    }
    
    # Calculate magnitude distribution
    for quake in nearby_quakes:
        mag = quake['properties'].get('mag', 0)
        if mag < 3.0:
            mag_bins['0-2.9'] += 1
        elif mag < 4.0:
            mag_bins['3.0-3.9'] += 1
        elif mag < 5.0:
            mag_bins['4.0-4.9'] += 1
        elif mag < 6.0:
            mag_bins['5.0-5.9'] += 1
        else:
            mag_bins['6.0+'] += 1
    
    # Calculate time-based statistics (last 24h, last 7d, last 30d)
    now = datetime.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    time_stats = {
        'last_24h': 0,
        'last_7d': 0,
        'last_30d': 0
    }
    
    for quake in nearby_quakes:
        time_ms = quake['properties'].get('time', 0)
        quake_time = datetime.fromtimestamp(time_ms / 1000)
        
        if quake_time >= last_24h:
            time_stats['last_24h'] += 1
        
        if quake_time >= last_7d:
            time_stats['last_7d'] += 1
            
        if quake_time >= last_30d:
            time_stats['last_30d'] += 1
    
    # Return analysis results
    return {
        'center': {
            'latitude': lat,
            'longitude': lon
        },
        'radius': radius,
        'total_earthquakes': total_count,
        'magnitude_distribution': mag_bins,
        'time_statistics': time_stats,
        'nearby_earthquakes': nearby_quakes
    }

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
        
    Returns:
        float: Distance in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    # Calculate the distance
    distance = c * r
    return distance

# New functions using OpenQuake

def create_point_source(latitude, longitude, a_val=4.5):
    """Create a simple point source for a given location"""
    # Define a point source at the given coordinates
    point_source = PointSource(
        source_id='POINT_1',
        name='Example Point Source',
        tectonic_region_type='Active Shallow Crust',
        mfd=TruncatedGRMFD(
            a_val=a_val,  # Activity rate (events per year)
            b_val=1.0,  # b-value of the Gutenberg-Richter relation
            min_mag=5.0,  # Minimum magnitude
            max_mag=7.5,  # Maximum magnitude
            bin_width=0.1  # Width of the magnitude bin
        ),
        nodal_plane_distribution=geo.NodalPlane.as_probability_distribution(
            [(1.0, geo.NodalPlane(strike=0.0, dip=90.0, rake=0.0))]
        ),
        hypocenter_distribution=geo.HypocenterDepthDistribution(
            [(0.5, 5.0), (0.5, 10.0)]  # (probability, depth)
        ),
        upper_seismogenic_depth=0.0,  # km
        lower_seismogenic_depth=30.0,  # km
        magnitude_scaling_relationship=WC1994(),
        rupture_aspect_ratio=1.0,
        temporal_occurrence_model=None,  # Use default Poissonian model
        location=geo.Point(longitude, latitude)
    )
    return point_source

def estimate_seismicity_param(earthquakes, lat, lon, radius=300):
    """
    Estimate seismicity parameters based on historical earthquake data
    
    Args:
        earthquakes (dict): Dictionary containing earthquake data
        lat (float): Latitude of the point of interest
        lon (float): Longitude of the point of interest
        radius (float): Radius around the point in kilometers
        
    Returns:
        float: Estimated a-value for Gutenberg-Richter relation
    """
    # Extract features from earthquakes
    features = earthquakes.get('features', []) if isinstance(earthquakes, dict) else []
    
    # Find earthquakes within radius
    nearby_mags = []
    for quake in features:
        if 'geometry' not in quake or 'coordinates' not in quake['geometry']:
            continue
            
        quake_coords = quake['geometry']['coordinates']
        if len(quake_coords) < 2:
            continue
            
        quake_lon, quake_lat = quake_coords[0], quake_coords[1]
        
        # Calculate distance (simplified haversine)
        distance = calculate_distance(lat, lon, quake_lat, quake_lon)
        
        if distance <= radius and 'properties' in quake and 'mag' in quake['properties']:
            nearby_mags.append(quake['properties']['mag'])
    
    # If we don't have enough earthquakes, return default a-value
    if len(nearby_mags) < 5:
        return 4.5  # Default a-value
    
    # Estimate a-value and b-value using MLE
    # Simple approach for demo purposes
    b_value = 1.0  # Assume standard b-value
    mags = np.array(nearby_mags)
    mags = mags[mags >= 4.0]  # Only consider M4.0+ for completeness
    
    if len(mags) == 0:
        return 4.5  # Default
    
    # Estimate a-value based on frequency-magnitude distribution
    min_mag = 4.0
    mag_range = np.max(mags) - min_mag
    
    # Simple estimation
    n_eq = len(mags)
    years = 30.0  # Assume 30 years of data
    area = math.pi * radius * radius
    
    # Normalize to 1 year and standard area
    a_val = math.log10(n_eq / years) + b_value * min_mag
    
    # Clamp the result to reasonable values
    a_val = max(3.0, min(6.0, a_val))
    
    return a_val

def perform_openquake_hazard_analysis(latitude, longitude, earthquakes=None, intensity_measure_type='PGA'):
    """
    Perform a basic seismic hazard analysis for the given coordinates using OpenQuake
    
    Args:
        latitude (float): Site latitude
        longitude (float): Site longitude
        earthquakes (dict, optional): Dictionary containing earthquake data
        intensity_measure_type (str): Type of intensity measure (default: PGA)
        
    Returns:
        dict: Hazard analysis results
    """
    try:
        # Create a site collection with a single site
        site = geo.Site(
            location=geo.Point(longitude, latitude),
            vs30=760.0,  # Default value for rock site in m/s
            vs30measured=False,
            z1pt0=100.0,  # Depth to Vs=1.0 km/s
            z2pt5=5.0,    # Depth to Vs=2.5 km/s
        )
        sites = geo.SiteCollection([site])
        
        # Estimate a-value if we have earthquake data
        a_val = 4.5  # Default
        if earthquakes:
            a_val = estimate_seismicity_param(earthquakes, latitude, longitude)
        
        # Create a source model with a point source
        source = create_point_source(latitude, longitude, a_val)
        
        # Set up the ground motion model (GMPE)
        gsim = BooreAtkinson2008()
        
        # Define intensity measure type and levels
        if intensity_measure_type == 'PGA':
            imtls = {imt.PGA(): [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527, 0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778, 1.09, 1.52, 2.13]}
        elif intensity_measure_type == 'SA(1.0)':
            imtls = {imt.SA(1.0): [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527, 0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778, 1.09, 1.52, 2.13]}
        else:
            raise ValueError(f"Unsupported intensity measure type: {intensity_measure_type}")
        
        # Calculate hazard curves
        ctx_provider = filters.ContextMaker(
            trt_rlzs=[(source.tectonic_region_type, gsim)],
            src_filter=filters.SourceFilter(sites, 200)  # 200 km maximum distance
        )
        
        curves = hazard_curve.calc_hazard_curves(
            [source], ctx_provider, imtls
        )
        
        # Process results for JSON response
        result = {}
        for imt_key, curve in curves.items():
            # Convert numpy arrays to lists for JSON serialization
            levels = [float(level) for level in imtls[imt_key]]
            poes = [float(poe) for poe in curve[0]]  # First site
            
            result[str(imt_key)] = {
                'levels': levels,
                'poes': poes,
                # Calculate risk scores (simplified example)
                'risk_score': calculate_risk_score(levels, poes)
            }
        
        return {
            'status': 'success',
            'site': {'latitude': latitude, 'longitude': longitude},
            'hazard_curves': result,
            'metadata': {
                'model': 'OpenQuake Simple Hazard Analysis',
                'intensity_measure_type': intensity_measure_type,
                'a_value': a_val
            }
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

def calculate_risk_score(levels, poes):
    """
    Calculate a simplified risk score based on hazard curves
    The score is calculated as the weighted sum of probability of exceedance
    
    Args:
        levels (list): Intensity measure levels
        poes (list): Probability of exceedance for each level
        
    Returns:
        float: Risk score between 0 and 100
    """
    # Simple weighted sum approach
    if not poes or not levels:
        return 0
        
    # Normalize levels to weights (higher levels have higher weights)
    max_level = max(levels)
    weights = [level/max_level for level in levels]
    
    # Calculate weighted sum
    weighted_sum = sum(poe * weight for poe, weight in zip(poes, weights))
    
    # Normalize to 0-100 scale
    max_possible = sum(weights)  # If all POEs were 1.0
    if max_possible == 0:
        return 0
        
    risk_score = (weighted_sum / max_possible) * 100
    return round(risk_score, 2)

def perform_hazard_analysis(earthquake_data, latitude, longitude, radius=300):
    """
    Perform basic hazard analysis based on earthquake data within a radius of a point.
    
    Args:
        earthquake_data: List of earthquake features
        latitude: Latitude of the point of interest
        longitude: Longitude of the point of interest
        radius: Radius in kilometers to consider
        
    Returns:
        Dictionary with hazard analysis results
    """
    try:
        # Convert radius from km to degrees (approximately)
        # 1 degree of latitude = ~111 km
        radius_degrees = radius / 111.0
        
        # Filter earthquakes within the radius
        nearby_earthquakes = []
        for eq in earthquake_data.get('features', []):
            eq_lat = eq['geometry']['coordinates'][1]
            eq_lng = eq['geometry']['coordinates'][0]
            
            # Simple distance calculation (Euclidean distance, not great for large distances but OK for this purpose)
            distance = ((eq_lat - latitude) ** 2 + (eq_lng - longitude) ** 2) ** 0.5
            
            if distance <= radius_degrees:
                # Add distance to the earthquake data
                eq['distance'] = distance * 111.0  # Convert back to km
                nearby_earthquakes.append(eq)
        
        # Calculate statistics
        total_earthquakes = len(nearby_earthquakes)
        
        # Calculate probability based on earthquake count and magnitudes
        # This is a simplified model for demonstration purposes
        if total_earthquakes == 0:
            probability = 0.01  # Base probability
            risk_level = "Low"
        else:
            # Calculate average magnitude
            total_magnitude = sum(eq['properties']['mag'] for eq in nearby_earthquakes)
            avg_magnitude = total_magnitude / total_earthquakes if total_earthquakes > 0 else 0
            
            # Find maximum magnitude
            max_magnitude = max((eq['properties']['mag'] for eq in nearby_earthquakes), default=0)
            
            # Calculate recency factor (more recent earthquakes indicate higher risk)
            now = datetime.now().timestamp() * 1000  # Convert to milliseconds
            recency_sum = sum(1 / (max(1, (now - eq['properties']['time']) / 86400000)) for eq in nearby_earthquakes)
            recency_factor = min(1.0, recency_sum / 10)  # Normalize, with a cap at 1.0
            
            # Calculate probability - simple model based on count, magnitude, and recency
            base_probability = min(0.8, total_earthquakes / 100)  # More earthquakes = higher probability
            magnitude_factor = min(1.5, avg_magnitude / 3)  # Higher magnitude = higher probability
            
            # Combined probability
            probability = min(0.95, base_probability * magnitude_factor * (1 + recency_factor))
            
            # Determine risk level
            if probability < 0.3:
                risk_level = "Low"
            elif probability < 0.6:
                risk_level = "Moderate"
            elif probability < 0.8:
                risk_level = "High"
            else:
                risk_level = "Very High"
        
        # Return analysis results
        return {
            "probability": probability,
            "risk_level": risk_level,
            "nearby_earthquakes": total_earthquakes,
            "analysis_date": datetime.now().isoformat(),
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "radius_km": radius
            }
        }
    except Exception as e:
        print(f"Error in perform_hazard_analysis: {str(e)}")
        # Return a minimal result with error information
        return {
            "probability": 0.1,  # Default low probability
            "risk_level": "Unknown",
            "error": str(e),
            "nearby_earthquakes": 0
        }

def get_seismic_hazard_summary(latitude, longitude, earthquakes=None):
    """
    Get a simplified hazard summary for quick display
    
    Args:
        latitude (float): Site latitude
        longitude (float): Site longitude
        earthquakes (dict, optional): Dictionary containing earthquake data
        
    Returns:
        dict: Simplified hazard results
    """
    # Perform full analysis
    full_result = perform_openquake_hazard_analysis(latitude, longitude, earthquakes)
    
    if full_result['status'] == 'error':
        return full_result
    
    # Extract key information for simplified display
    hazard_curves = full_result.get('hazard_curves', {})
    
    # Get the risk score for PGA if available
    risk_score = None
    for imt_type, data in hazard_curves.items():
        if 'PGA' in imt_type:
            risk_score = data.get('risk_score', 0)
            break
    
    # If no PGA, use the first available IMT
    if risk_score is None and hazard_curves:
        first_imt = next(iter(hazard_curves.values()))
        risk_score = first_imt.get('risk_score', 0)
    
    # Create hazard categories based on risk score
    hazard_category = 'Low'
    if risk_score > 60:
        hazard_category = 'High'
    elif risk_score > 30:
        hazard_category = 'Moderate'
    
    # Get estimated PGA with 10% probability in 50 years
    pga_10_50 = estimate_pga_probability(hazard_curves.get('PGA()', {}).get('levels', []), 
                                         hazard_curves.get('PGA()', {}).get('poes', []),
                                         probability=0.1, 
                                         time_years=50)
    
    return {
        'status': 'success',
        'site': {'latitude': latitude, 'longitude': longitude},
        'hazard_summary': {
            'risk_score': risk_score if risk_score is not None else 0,
            'category': hazard_category,
            'description': f"This location has a {hazard_category.lower()} seismic hazard level.",
            'pga_10_50': pga_10_50,
            'pga_10_50_description': f"PGA with 10% probability of exceedance in 50 years: {pga_10_50:.3f}g",
            'a_value': full_result.get('metadata', {}).get('a_value', 4.5)
        }
    }

def estimate_pga_probability(levels, poes, probability=0.1, time_years=50):
    """
    Estimate the PGA value for a given probability and time period
    using linear interpolation of the hazard curve
    
    Args:
        levels (list): Intensity measure levels
        poes (list): Annual probability of exceedance for each level
        probability (float): Target probability of exceedance (e.g., 0.1 for 10%)
        time_years (int): Time period in years (e.g., 50 for 50 years)
        
    Returns:
        float: Estimated PGA value
    """
    if not levels or not poes or len(levels) != len(poes):
        return 0.0
    
    # Convert from annual probability to probability over time_years
    target_annual_prob = 1 - (1 - probability) ** (1 / time_years)
    
    # Find the closest values
    for i in range(len(poes) - 1):
        if poes[i] >= target_annual_prob >= poes[i+1]:
            # Linear interpolation in log space
            log_level1 = math.log(levels[i])
            log_level2 = math.log(levels[i+1])
            log_poe1 = math.log(poes[i])
            log_poe2 = math.log(poes[i+1])
            
            log_target = math.log(target_annual_prob)
            log_result = log_level1 + (log_target - log_poe1) * (log_level2 - log_level1) / (log_poe2 - log_poe1)
            
            return round(math.exp(log_result), 3)
    
    # If no suitable range found, return the closest value
    if target_annual_prob > poes[0]:
        return round(levels[0], 3)
    elif target_annual_prob < poes[-1]:
        return round(levels[-1], 3)
    else:
        return 0.0