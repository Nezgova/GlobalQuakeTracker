"""
Enhanced earthquake prediction module using OpenQuake engine and statistical methods
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math
from scipy import stats
import random
import traceback
import json

# OpenQuake imports
from openquake.hazardlib import geo, const, mfd, source, imt, gsim
from openquake.hazardlib.source import AreaSource, PointSource, CharacteristicFaultSource
from openquake.hazardlib.geo import Point, Polygon, NodalPlane, Line, SimpleFaultSurface
from openquake.hazardlib.sourceconverter import SourceConverter
#from openquake.hazardlib.calc.stochastic import stochastic_event_set
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.contexts import ContextMaker, RuptureContext
from openquake.hazardlib.scalerel import WC1994  # Keep only valid ones
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.pmf import PMF

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
                                'magnitude': props['mag'] if props['mag'] is not None else 0
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
                peak_period = 1/f[max_idx] if f[max_idx] > 0 and max_idx > 0 else 0
                periodicity = peak_period if peak_period < 365 else 0  # Cap at 1 year
            except Exception as e:
                print(f"Error in FFT analysis: {str(e)}")
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

def estimate_focal_mechanisms(earthquakes):
    """
    Estimate predominant focal mechanisms in the area from historical data
    Returns a list of NodalPlane objects with weights
    """
    # Default focal mechanisms (used when insufficient data)
    default_nodal_planes = [
        NodalPlane(strike=0, dip=90, rake=0),  # Strike-slip
        NodalPlane(strike=0, dip=45, rake=90),  # Reverse
        NodalPlane(strike=0, dip=45, rake=-90)  # Normal
    ]
    default_weights = [0.5, 0.25, 0.25]  # Strike-slip is most common globally
    
    try:
        # If not enough data, return defaults
        if not earthquakes or len(earthquakes) < 10:
            return PMF([(weight, plane) for weight, plane in zip(default_weights, default_nodal_planes)])
        
        # Extract focal mechanisms if available
        strike_data = []
        dip_data = []
        rake_data = []
        
        for eq in earthquakes:
            try:
                if isinstance(eq, dict) and 'properties' in eq:
                    props = eq['properties']
                    # Check if focal mechanism data exists
                    if all(k in props for k in ['strike', 'dip', 'rake']):
                        strike_data.append(props['strike'])
                        dip_data.append(props['dip'])
                        rake_data.append(props['rake'])
            except Exception:
                continue
        
        # If we have focal mechanism data
        if len(strike_data) >= 5:
            # Cluster the focal mechanisms
            from sklearn.cluster import KMeans
            
            # Prepare data for clustering
            focal_data = np.column_stack((
                np.cos(np.radians(strike_data)) * np.sin(np.radians(dip_data)),
                np.sin(np.radians(strike_data)) * np.sin(np.radians(dip_data)),
                np.cos(np.radians(dip_data)) * np.cos(np.radians(rake_data))
            ))
            
            # Determine optimal number of clusters (max 3)
            n_clusters = min(3, len(focal_data) // 5 + 1)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            kmeans.fit(focal_data)
            
            # Get cluster centers and calculate weights
            cluster_labels = kmeans.labels_
            unique_labels, counts = np.unique(cluster_labels, return_counts=True)
            weights = counts / counts.sum()
            
            # Convert cluster centers back to strike, dip, rake
            nodal_planes = []
            for i, center in enumerate(kmeans.cluster_centers_):
                # This is a simplification; proper conversion would be more complex
                x, y, z = center
                strike = math.degrees(math.atan2(y, x)) % 360
                dip = math.degrees(math.acos(z))
                
                # Estimate rake (simplified)
                rake_cluster = [rake_data[j] for j, label in enumerate(cluster_labels) if label == i]
                rake = np.median(rake_cluster) if rake_cluster else 0
                
                nodal_planes.append(NodalPlane(strike=strike, dip=dip, rake=rake))
            
            return PMF([(weight, plane) for weight, plane in zip(weights, nodal_planes)])
        
        # If no focal mechanism data available, return defaults
        return PMF([(weight, plane) for weight, plane in zip(default_weights, default_nodal_planes)])
        
    except Exception as e:
        print(f"Error estimating focal mechanisms: {str(e)}")
        traceback.print_exc()
        # Return default focal mechanisms on error
        return PMF([(weight, plane) for weight, plane in zip(default_weights, default_nodal_planes)])

def create_source_model(lat, lon, earthquakes, magnitude_dist, temporal_patterns, radius_km=500):
    """
    Create OpenQuake source model based on historical earthquake data
    
    Args:
        lat, lon: Target location
        earthquakes: Historical earthquake data
        magnitude_dist: Gutenberg-Richter parameters
        temporal_patterns: Temporal pattern analysis results
        radius_km: Radius around target location to consider
        
    Returns:
        List of OpenQuake source objects
    """
    sources = []
    
    try:
        if not earthquakes or len(earthquakes) < 10:
            return sources
            
        # Create area source around the target location
        center_point = Point(lon, lat)
        
        # Create polygon for area source (simplified circular area)
        azimuths = list(range(0, 360, 10))
        points = []
        
        for azimuth in azimuths:
            # Calculate point at radius_km distance in azimuth direction
            point = geo.point.Point.from_distance(
                center_point,
                azimuth=azimuth,
                distance=radius_km
            )
            points.append((point.longitude, point.latitude))
            
        # Create polygon
        polygon = Polygon([Point(lon, lat) for lon, lat in points])
        
        # Extract b-value from magnitude distribution or use default
        b_value = magnitude_dist.get("b_value", 1.0)
        if b_value <= 0 or b_value > 2.5:
            b_value = 1.0  # Default b-value if invalid
        
        # Calculate a-value adjusted for the area
        a_value = magnitude_dist.get("a_value", 0)
        if a_value <= 0:
            # Estimate from event count
            num_events = len(earthquakes)
            years_of_data = 10  # Assume 10 years of data if not specified
            a_value = math.log10(num_events / years_of_data) + b_value * 4.0  # 4.0 is min magnitude
        
        # Determine min and max magnitudes
        magnitudes = [eq['properties']['mag'] for eq in earthquakes 
                     if isinstance(eq, dict) and 'properties' in eq and 'mag' in eq['properties']]
        
        min_mag = 4.0  # Minimum magnitude of interest
        if magnitudes:
            max_mag = min(max(magnitudes) + 0.5, 9.0)  # Max historical plus 0.5, capped at 9.0
        else:
            max_mag = 7.5  # Default
        
        # Create Gutenberg-Richter MFD
        occurrence_rate = 10 ** (a_value - b_value * min_mag)
        mfd_model = mfd.TruncatedGRMFD(
            min_mag=min_mag,
            max_mag=max_mag,
            bin_width=0.1,
            a_val=a_value,
            b_val=b_value
        )
        
        # Estimate focal mechanisms
        nodal_planes = estimate_focal_mechanisms(earthquakes)
        
        # Estimate hypocentral depth distribution
        depths = [eq['geometry']['coordinates'][2] for eq in earthquakes 
                 if isinstance(eq, dict) and 'geometry' in eq and 
                 isinstance(eq['geometry'].get('coordinates'), list) and 
                 len(eq['geometry']['coordinates']) > 2]
        
        if depths:
            # Create depth PMF from historical data
            depth_bins = np.linspace(0, 50, 6)  # 0-10, 10-20, ..., 40-50 km
            hist, _ = np.histogram(depths, bins=depth_bins)
            if sum(hist) > 0:
                depth_weights = hist / sum(hist)
                depth_pmf = PMF([(weight, (depth_bins[i] + depth_bins[i+1])/2) 
                                for i, weight in enumerate(depth_weights) if weight > 0])
            else:
                depth_pmf = PMF([(0.5, 10), (0.3, 20), (0.2, 30)])
        else:
            depth_pmf = PMF([(0.5, 10), (0.3, 20), (0.2, 30)])  # Default depth distribution
            
        # Create area source
        source_id = f"AREA_{lat:.2f}_{lon:.2f}"
        area_source = AreaSource(
            source_id=source_id,
            name=f"Area source around {lat:.2f}, {lon:.2f}",
            tectonic_region_type="Active Shallow Crust",
            mfd=mfd_model,
            rupture_mesh_spacing=5.0,
            magnitude_scaling_relationship=WC1994(),
            rupture_aspect_ratio=1.5,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=50.0,
            nodal_plane_distribution=nodal_planes,
            hypocenter_distribution=depth_pmf,
            polygon=polygon,
            area_discretization=50.0,
            temporal_occurrence_model=None  # Uses Poissonian by default
        )
        
        sources.append(area_source)
        
        # Add point sources for significant recent events (potential aftershock sequences)
        if temporal_patterns.get("pattern") == "clustered":
            try:
                # Sort by time (most recent first) and magnitude (highest first)
                recent_significant = sorted(
                    [eq for eq in earthquakes if isinstance(eq, dict) and 
                     'properties' in eq and 'mag' in eq['properties'] and 
                     eq['properties']['mag'] is not None and eq['properties']['mag'] >= 5.0],
                    key=lambda x: (-(x['properties']['time'] if isinstance(x['properties']['time'], (int, float)) else 0), 
                                  -(x['properties']['mag']))
                )[:3]  # Top 3 significant events
                
                for i, eq in enumerate(recent_significant):
                    # Get coordinates
                    coords = eq['geometry']['coordinates']
                    eq_lon, eq_lat = coords[0], coords[1]
                    depth = coords[2] if len(coords) > 2 else 10.0
                    
                    # Main shock magnitude
                    main_mag = eq['properties']['mag']
                    
                    # Create MFD for aftershock sequence
                    # Båth's law: largest aftershock is ~1.2 magnitude units smaller than mainshock
                    aftershock_a_val = a_value * 0.8  # Reduced rate
                    aftershock_mfd = mfd.TruncatedGRMFD(
                        min_mag=min_mag,
                        max_mag=main_mag - 0.5,  # Max aftershock mag
                        bin_width=0.1,
                        a_val=aftershock_a_val,
                        b_val=b_value
                    )
                    
                    # Create point source for aftershock sequence
                    point_source = PointSource(
                        source_id=f"POINT_{eq_lat:.2f}_{eq_lon:.2f}_{i}",
                        name=f"Recent significant event at {eq_lat:.2f}, {eq_lon:.2f}",
                        tectonic_region_type="Active Shallow Crust",
                        mfd=aftershock_mfd,
                        rupture_mesh_spacing=2.0,
                        magnitude_scaling_relationship=WC1994(),
                        rupture_aspect_ratio=1.5,
                        upper_seismogenic_depth=max(0, depth - 10),
                        lower_seismogenic_depth=min(50, depth + 10),
                        location=Point(eq_lon, eq_lat),
                        nodal_plane_distribution=nodal_planes,
                        hypocenter_distribution=PMF([(1.0, depth)])
                    )
                    
                    sources.append(point_source)
            except Exception as e:
                print(f"Error creating point sources: {str(e)}")
                traceback.print_exc()
                
        return sources
        
    except Exception as e:
        print(f"Error creating source model: {str(e)}")
        traceback.print_exc()
        return sources

def run_openquake_simulation(target_lat, target_lon, sources, time_horizon=30, intensity_threshold=4.0):
    """
    Run OpenQuake simulation to predict events
    
    Args:
        target_lat, target_lon: Target location coordinates
        sources: OpenQuake source objects
        time_horizon: Time horizon in days
        intensity_threshold: Minimum magnitude threshold
        
    Returns:
        List of predicted events
    """
    predictions = []
    
    try:
        if not sources:
            return predictions
            
        # Create site collection (just the target location)
        sites = SiteCollection([Site(location=Point(target_lon, target_lat),
                                    vs30=760,  # Generic rock site
                                    vs30measured=False,
                                    z1pt0=100.0,
                                    z2pt5=1.0)])
        
        # Calculate annual occurrence rates
        investigation_time_years = time_horizon / 365.25
        
        # Select appropriate GMPEs
        gsims = {'Active Shallow Crust': gsim.Campbell2003()}
        
        # Create context maker
        ctx_maker = ContextMaker(gsims)
        
        # Generate stochastic event set
        stochastic_events = []
        for source in sources:
            try:
                # Get all possible ruptures from the source
                ruptures = list(source.iter_ruptures())
                
                for rupture in ruptures:
                    # Calculate occurrence rate for this rupture
                    occurrence_rate = rupture.occurrence_rate
                    
                    # Skip low magnitude events
                    if rupture.mag < intensity_threshold:
                        continue
                    
                    # Calculate probability of this event within the time period
                    probability = 1 - math.exp(-occurrence_rate * investigation_time_years)
                    
                    # Skip very low probability events
                    if probability < 0.01:
                        continue
                    
                    # Randomly determine if this event occurs in our simulation
                    if random.random() <= probability:
                        # Record event details
                        ctx = ctx_maker.make_contexts(sites, rupture)[0]
                        
                        # Calculate random time within the forecast period
                        days_from_now = random.uniform(0, time_horizon)
                        
                        stochastic_events.append({
                            "magnitude": rupture.mag,
                            "days_from_now": days_from_now,
                            "probability": probability,
                            "location": {
                                "latitude": rupture.hypocenter.latitude,
                                "longitude": rupture.hypocenter.longitude,
                                "depth": rupture.hypocenter.depth
                            },
                            "distance_km": calculate_distance(
                                target_lat, target_lon,
                                rupture.hypocenter.latitude, rupture.hypocenter.longitude
                            ),
                            "tectonic_region": rupture.tectonic_region_type
                        })
            except Exception as e:
                print(f"Error processing source in OpenQuake simulation: {str(e)}")
                continue
                
        # If we have events, sort them by time and format for output
        if stochastic_events:
            # Sort by time
            stochastic_events.sort(key=lambda x: x["days_from_now"])
            
            # Build predictions
            current_time = datetime.now()
            
            for event in stochastic_events:
                predicted_time = current_time + timedelta(days=event["days_from_now"])
                
                predictions.append({
                    "predicted_time": predicted_time.isoformat(),
                    "days_from_now": round(event["days_from_now"], 1),
                    "estimated_magnitude": round(event["magnitude"], 1),
                    "probability": round(event["probability"], 2),
                    "prediction_type": "oq_simulation",
                    "location": {
                        "latitude": event["location"]["latitude"],
                        "longitude": event["location"]["longitude"],
                        "depth_km": round(event["location"]["depth"], 1)
                    },
                    "distance_km": round(event["distance_km"], 1)
                })
        
        return predictions
        
    except Exception as e:
        print(f"Error running OpenQuake simulation: {str(e)}")
        traceback.print_exc()
        return predictions

def predict_future_earthquakes(lat, lon, earthquakes, time_horizon=30, intensity_threshold=4.0):
    """
    Predict future earthquakes using OpenQuake engine and statistical methods
    
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
        
        # Create OpenQuake source model
        sources = create_source_model(lat, lon, nearby_earthquakes, magnitude_dist, temporal_patterns)
        print(f"Created {len(sources)} source objects for OpenQuake modeling")
        
        if not sources:
            print("Failed to create OpenQuake source model, falling back to statistical methods")
        
        # Generate predictions using OpenQuake
        oq_predictions = []
        if sources:
            oq_predictions = run_openquake_simulation(lat, lon, sources, time_horizon, intensity_threshold)
            print(f"OpenQuake simulation generated {len(oq_predictions)} predictions")
            
        # Generate prediction
        predictions = []
        
        # Combine OpenQuake predictions with statistical ones
        predictions.extend(oq_predictions)
        
        # If we don't have enough predictions from OpenQuake, supplement with statistical methods
        if len(predictions) < 3:
            print("Supplementing with statistical predictions")
            
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
                                    "predicted_time": (datetime.now() + timedelta(days=days_offset)).isoformat(),
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
                                predicted_mag = max(avg_mag * random.uniform(0.8, 1.2), intensity_threshold)
                                
                            predictions.append({
                                "predicted_time": (datetime.now() + timedelta(days=days_offset)).isoformat(),
                                "days_from_now": days_offset,
                                "estimated_magnitude": round(predicted_mag, 1),
                                "probability": 0.7 - (i * 0.1),  # Decreasing probability with time
                                "prediction_type": "periodic"
                            })
                except Exception as e:
                    print(f"Error in regular pattern prediction: {str(e)}")
                    traceback.print_exc()
            else:
                # For random pattern, use Poisson process
                try:
                    # Calculate average earthquakes per day
                    avg_time_diff = temporal_patterns.get("mean_interval", 7)
                    
                    # Use Poisson distribution to simulate random occurrences
                    events_in_period = np.random.poisson(time_horizon / avg_time_diff, size=1)[0]
                    events_in_period = min(events_in_period, 5)  # Limit predictions
                    
                    if events_in_period > 0:
                        # Generate random times within the time horizon
                        event_times = np.sort(np.random.uniform(0, time_horizon, size=events_in_period))
                        
                        for days_offset in event_times:
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
                                predicted_mag = max(avg_mag * random.uniform(0.8, 1.2), intensity_threshold)
                                
                            predictions.append({
                                "predicted_time": (datetime.now() + timedelta(days=days_offset)).isoformat(),
                                "days_from_now": round(days_offset, 1),
                                "estimated_magnitude": round(predicted_mag, 1),
                                "probability": 0.5,  # Standard probability for random model
                                "prediction_type": "poisson"
                            })
                except Exception as e:
                    print(f"Error in random pattern prediction: {str(e)}")
                    traceback.print_exc()
        
        # Sort by time (closest first)
        predictions = sorted(predictions, key=lambda x: x["days_from_now"])
        
        # Add risk assessment for each prediction
        for prediction in predictions:
            try:
                # Calculate risk factor based on magnitude and distance
                magnitude = prediction["estimated_magnitude"]
                
                # Different handling based on prediction type
                if "location" in prediction:
                    # OpenQuake predictions have location
                    distance_km = prediction["distance_km"]
                else:
                    # Statistical predictions - assume near target location (within 100km)
                    distance_km = random.uniform(20, 100)
                    prediction["distance_km"] = round(distance_km, 1)
                    
                    # Add location estimate
                    # Random point near target (but not exactly at target to avoid alarm)
                    bearing = random.uniform(0, 360)
                    point = geo.point.Point.from_distance(
                        Point(lon, lat),
                        azimuth=bearing,
                        distance=distance_km
                    )
                    prediction["location"] = {
                        "latitude": point.latitude,
                        "longitude": point.longitude,
                        "depth_km": round(random.uniform(5, 30), 1)  # Random depth
                    }
                
                # Calculate risk factor
                # Higher magnitude and closer distance mean higher risk
                risk_factor = (magnitude ** 2) / max(distance_km, 10)
                
                # Classify risk
                if risk_factor > 5:
                    risk_level = "high"
                elif risk_factor > 1:
                    risk_level = "moderate"
                else:
                    risk_level = "low"
                    
                prediction["risk_assessment"] = {
                    "risk_factor": round(risk_factor, 2),
                    "risk_level": risk_level
                }
            except Exception as e:
                print(f"Error in risk assessment: {str(e)}")
                prediction["risk_assessment"] = {"risk_level": "unknown"}
                continue
        
        # Calculate confidence score based on data quality
        confidence_score = 0.0
        
        # Factors affecting confidence:
        # 1. Number of nearby earthquakes
        if len(nearby_earthquakes) >= 100:
            confidence_score += 0.3
        elif len(nearby_earthquakes) >= 50:
            confidence_score += 0.2
        elif len(nearby_earthquakes) >= 20:
            confidence_score += 0.1
            
        # 2. Quality of G-R relationship
        if magnitude_dist.get("r_squared", 0) > 0.9:
            confidence_score += 0.3
        elif magnitude_dist.get("r_squared", 0) > 0.7:
            confidence_score += 0.2
        elif magnitude_dist.get("r_squared", 0) > 0.5:
            confidence_score += 0.1
            
        # 3. Temporal pattern clarity
        if temporal_patterns.get("pattern") != "insufficient_data":
            if temporal_patterns.get("cv", 0) > 0 and temporal_patterns.get("mean_interval", 0) > 0:
                confidence_score += 0.2
            else:
                confidence_score += 0.1
                
        # 4. Whether OpenQuake model was used
        if sources and len(oq_predictions) > 0:
            confidence_score += 0.2
            
        # Cap confidence at 0.9 (never 100% confident)
        confidence_score = min(max(confidence_score, 0.1), 0.9)
        
        # Prepare final response
        response = {
            "status": "success",
            "target_location": {
                "latitude": lat,
                "longitude": lon
            },
            "analysis_details": {
                "temporal_pattern": temporal_patterns.get("pattern", "unknown"),
                "periodicity_days": temporal_patterns.get("periodicity", 0),
                "magnitude_distribution": {
                    "a_value": magnitude_dist.get("a_value", 0),
                    "b_value": magnitude_dist.get("b_value", 0)
                },
                "data_points_used": len(nearby_earthquakes),
                "time_horizon_days": time_horizon,
                "intensity_threshold": intensity_threshold,
                "confidence_score": round(confidence_score, 2)
            },
            "predictions": predictions[:10],  # Limit to top 10 predictions
            "prediction_count": len(predictions)
        }
        
        print(f"Prediction complete with {len(predictions)} events predicted")
        return response
        
    except Exception as e:
        print(f"Error in earthquake prediction: {str(e)}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to generate prediction: {str(e)}",
            "predictions": []
        }

def perform_simple_statistical_forecast(lat, lon, earthquakes, time_horizon=30):
    """
    Simplified statistical forecast method without OpenQuake dependency
    For use when OpenQuake is not available
    """
    try:
        # Filter earthquakes within 500km radius
        nearby_earthquakes = []
        for eq in earthquakes:
            try:
                if not isinstance(eq, dict) or 'geometry' not in eq:
                    continue
                
                coords = eq['geometry']['coordinates']
                if len(coords) < 2:
                    continue
                
                eq_lon, eq_lat = coords[0], coords[1]
                
                # Calculate distance
                distance = calculate_distance(lat, lon, eq_lat, eq_lon)
                if distance <= 500:  # 500km radius
                    nearby_earthquakes.append(eq)
            except Exception:
                continue
                
        if len(nearby_earthquakes) < 5:
            return {"status": "insufficient_data", "predictions": []}
        
        # Extract magnitudes and calculate statistics
        magnitudes = []
        for eq in nearby_earthquakes:
            try:
                mag = eq['properties']['mag']
                if mag is not None:
                    magnitudes.append(mag)
            except (KeyError, TypeError):
                continue
                
        if not magnitudes:
            return {"status": "insufficient_data", "predictions": []}
            
        # Calculate basic statistics
        avg_mag = np.mean(magnitudes)
        max_mag = max(magnitudes)
        
        # Count events in the past month
        recent_count = 0
        one_month_ago = datetime.now() - timedelta(days=30)
        
        for eq in nearby_earthquakes:
            try:
                if isinstance(eq['properties']['time'], (int, float)):
                    eq_time = datetime.fromtimestamp(eq['properties']['time']/1000)
                    if eq_time >= one_month_ago:
                        recent_count += 1
            except (KeyError, TypeError, ValueError):
                continue
                
        # Estimate monthly rate
        monthly_rate = max(recent_count, 1)
        
        # Estimate rate for the forecast period
        forecast_rate = monthly_rate * (time_horizon / 30)
        
        # Generate predictions
        predictions = []
        num_predictions = min(int(forecast_rate) + 1, 5)  # Cap at 5 predictions
        
        for i in range(num_predictions):
            # Generate random time within forecast period
            days_offset = random.uniform(0, time_horizon)
            
            # Generate magnitude (tend toward average with some outliers)
            if random.random() < 0.8:
                # Normal case - near average
                predicted_mag = random.uniform(avg_mag - 0.5, avg_mag + 0.5)
            else:
                # Occasional larger event
                predicted_mag = random.uniform(avg_mag, max_mag + 0.3)
                
            predicted_mag = max(4.0, min(predicted_mag, 7.5))  # Cap magnitude range
            
            # Generate random location within 100km of target
            bearing = random.uniform(0, 360)
            distance = random.uniform(20, 100)
            
            predictions.append({
                "predicted_time": (datetime.now() + timedelta(days=days_offset)).isoformat(),
                "days_from_now": round(days_offset, 1),
                "estimated_magnitude": round(predicted_mag, 1),
                "probability": 0.5,  # Fixed probability for simple model
                "prediction_type": "statistical",
                "distance_km": round(distance, 1),
                "risk_assessment": {
                    "risk_level": "moderate" if predicted_mag >= 5.0 else "low"
                }
            })
            
        # Sort by time
        predictions.sort(key=lambda x: x["days_from_now"])
        
        return {
            "status": "success",
            "target_location": {"latitude": lat, "longitude": lon},
            "analysis_details": {
                "data_points_used": len(nearby_earthquakes),
                "average_magnitude": round(avg_mag, 2),
                "monthly_rate": monthly_rate,
                "confidence_score": 0.3  # Fixed low confidence for simple model
            },
            "predictions": predictions,
            "prediction_count": len(predictions)
        }
        
    except Exception as e:
        print(f"Error in simple statistical forecast: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": str(e), "predictions": []}


def export_prediction_to_geojson(prediction_results, filename=None):
    """
    Export earthquake prediction results to GeoJSON format
    
    Args:
        prediction_results: The prediction results dictionary
        filename: Optional filename to save the GeoJSON
        
    Returns:
        GeoJSON string and optionally saves to file
    """
    try:
        # Create GeoJSON structure
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "generated": datetime.now().isoformat(),
                "title": "Earthquake Prediction Results",
                "target_location": prediction_results.get("target_location", {}),
                "analysis_details": prediction_results.get("analysis_details", {})
            },
            "features": []
        }
        
        # Add each prediction as a feature
        predictions = prediction_results.get("predictions", [])
        for pred in predictions:
            if "location" not in pred:
                continue
                
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        pred["location"]["longitude"],
                        pred["location"]["latitude"],
                        pred["location"].get("depth_km", 10)
                    ]
                },
                "properties": {
                    "predicted_time": pred["predicted_time"],
                    "days_from_now": pred["days_from_now"],
                    "estimated_magnitude": pred["estimated_magnitude"],
                    "probability": pred["probability"],
                    "prediction_type": pred.get("prediction_type", "unknown"),
                    "distance_km": pred.get("distance_km", 0),
                    "risk_level": pred.get("risk_assessment", {}).get("risk_level", "unknown")
                }
            }
            
            geojson["features"].append(feature)
            
        # Save to file if filename provided
        if filename:
            with open(filename, 'w') as f:
                json.dump(geojson, f, indent=2)
                
        return json.dumps(geojson, indent=2)
        
    except Exception as e:
        print(f"Error exporting prediction to GeoJSON: {str(e)}")
        traceback.print_exc()
        return None

# If module is run directly, perform a test prediction
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        try:
            test_lat = float(sys.argv[1])
            test_lon = float(sys.argv[2])
            
            print(f"Loading test earthquake data...")
            
            # Load test data
            try:
                with open("test_earthquake_data.json", "r") as f:
                    test_data = json.load(f)
                
                if "features" in test_data:
                    test_earthquakes = test_data["features"]
                else:
                    test_earthquakes = test_data
                    
                print(f"Loaded {len(test_earthquakes)} test earthquakes")
            except Exception as e:
                print(f"Error loading test data: {str(e)}")
                print("Using empty dataset for testing")
                test_earthquakes = []
            
            # Run prediction
            print(f"Testing prediction for location: {test_lat}, {test_lon}")
            results = predict_future_earthquakes(test_lat, test_lon, test_earthquakes)
            
            # Print results
            print(json.dumps(results, indent=2))
            
            # Export to GeoJSON
            export_prediction_to_geojson(results, "prediction_results.geojson")
            print("Results exported to prediction_results.geojson")
            
        except Exception as e:
            print(f"Error during test: {str(e)}")
            traceback.print_exc()
    else:
        print("Usage: python earthquake_prediction.py <latitude> <longitude>")
        print("Example: python earthquake_prediction.py 34.05 -118.25")