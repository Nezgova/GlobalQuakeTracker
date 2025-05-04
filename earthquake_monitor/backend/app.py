from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import threading
import time
from datetime import datetime, timedelta
import requests
import pandas as pd

from data_processor import fetch_earthquake_data, process_earthquake_data
from hazard_analysis import (
    perform_hazard_analysis,  # Keep original function for backward compatibility
    perform_openquake_hazard_analysis,  # Advanced analysis using OpenQuake
    get_seismic_hazard_summary  # Simplified summary for quick display
)
from report_generator import generate_report

app = Flask(__name__)
# Enable CORS with more specific settings
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# In-memory storage for earthquake data
earthquake_cache = {
    "last_updated": None,
    "data": None,
    "filtered_data": None
}

# Background data refresh timer (update every 30 minutes)
def background_data_refresh():
    while True:
        try:
            print("Refreshing earthquake data...")
            raw_data = fetch_earthquake_data()
            if raw_data:
                earthquake_cache["data"] = raw_data
                earthquake_cache["last_updated"] = datetime.now()
                print(f"Data refreshed at {earthquake_cache['last_updated']}")
            else:
                print("Failed to refresh data")
        except Exception as e:
            print(f"Error refreshing data: {str(e)}")
        
        # Sleep for 30 minutes
        time.sleep(30 * 60)

# Start background data refresh thread
refresh_thread = threading.Thread(target=background_data_refresh, daemon=True)
refresh_thread.start()

@app.route('/api/earthquakes', methods=['GET'])
def get_earthquakes():
    try:
        # Query parameters
        days = float(request.args.get('days', 1.0))  # Default to 1 day
        min_magnitude = float(request.args.get('magnitude', 1.0))  # Default to magnitude 1.0+
        period = request.args.get('period')  # Optional period parameter for backward compatibility
        
        # Handle period parameter if provided (for backward compatibility)
        if period:
            days_map = {
                'hour': 0.042,
                'day': 1,
                'week': 7,
                'month': 30
            }
            days = days_map.get(period, 1)
        
        # If we have no data or it's older than 30 minutes, fetch new data
        if earthquake_cache["data"] is None or earthquake_cache["last_updated"] is None or \
           (datetime.now() - earthquake_cache["last_updated"]) > timedelta(minutes=30):
            raw_data = fetch_earthquake_data()
            if raw_data:
                earthquake_cache["data"] = raw_data
                earthquake_cache["last_updated"] = datetime.now()
            else:
                return jsonify({"error": "Failed to fetch earthquake data"}), 500
        
        # Process and filter the data
        filtered_data = process_earthquake_data(
            earthquake_cache["data"], 
            days_ago=days, 
            min_magnitude=min_magnitude
        )
        
        earthquake_cache["filtered_data"] = filtered_data
        return jsonify(filtered_data)
    except Exception as e:
        print(f"Error in get_earthquakes: {str(e)}")
        return jsonify({"error": f"Failed to process request: {str(e)}"}), 500

@app.route('/api/analysis', methods=['POST', 'OPTIONS'])
def analyze_earthquakes():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
        
    try:
        data = request.json
        
        # Extract parameters
        lat = data.get('latitude')
        lon = data.get('longitude')
        radius = data.get('radius', 300)  # Default 300km radius
        analysis_type = data.get('analysisType', 'standard')  # New parameter for analysis type
        
        if not lat or not lon:
            return jsonify({"error": "Latitude and longitude are required"}), 400
        
        # Get the currently filtered data or use default parameters
        if earthquake_cache["filtered_data"] is None:
            earthquakes = process_earthquake_data(
                earthquake_cache["data"],
                days_ago=7,
                min_magnitude=4.0
            )
        else:
            earthquakes = earthquake_cache["filtered_data"]
        
        # Choose analysis method based on analysis_type
        if analysis_type == 'advanced':
            # Use the OpenQuake-based analysis
            analysis_results = perform_openquake_hazard_analysis(
                float(lat), 
                float(lon), 
                earthquakes
            )
        elif analysis_type == 'summary':
            # Use the simplified summary
            analysis_results = get_seismic_hazard_summary(
                float(lat), 
                float(lon), 
                earthquakes
            )
        else:
            # Use the original analysis for backward compatibility
            analysis_results = perform_hazard_analysis(
                earthquakes, 
                float(lat), 
                float(lon), 
                float(radius)
            )
        
        # Add the analysis type to the results
        analysis_results['analysis_type'] = analysis_type
        
        return jsonify(analysis_results)
    except Exception as e:
        print(f"Error in analyze_earthquakes: {str(e)}")
        return jsonify({"error": f"Failed to process request: {str(e)}"}), 500

@app.route('/api/advanced-analysis', methods=['POST', 'OPTIONS'])
def advanced_analysis():
    """New endpoint specifically for advanced OpenQuake analysis"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
        
    try:
        data = request.json
        
        # Extract parameters
        lat = data.get('latitude')
        lon = data.get('longitude')
        intensity_measure_type = data.get('intensityMeasureType', 'PGA')  # Default to PGA
        
        if not lat or not lon:
            return jsonify({"error": "Latitude and longitude are required"}), 400
        
        # Get the currently filtered data
        earthquakes = earthquake_cache["filtered_data"] or earthquake_cache["data"]
        
        # Perform OpenQuake analysis
        analysis_results = perform_openquake_hazard_analysis(
            float(lat), 
            float(lon), 
            earthquakes,
            intensity_measure_type
        )
        
        return jsonify(analysis_results)
    except Exception as e:
        print(f"Error in advanced_analysis: {str(e)}")
        return jsonify({"error": f"Failed to process request: {str(e)}"}), 500

@app.route('/api/hazard-summary', methods=['GET', 'POST', 'OPTIONS'])
def hazard_summary():
    """New endpoint for quick hazard summary"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        # Handle both GET and POST requests
        if request.method == 'GET':
            lat = request.args.get('latitude')
            lon = request.args.get('longitude')
        else:  # POST
            data = request.json
            lat = data.get('latitude')
            lon = data.get('longitude')
        
        if not lat or not lon:
            return jsonify({"error": "Latitude and longitude are required"}), 400
        
        # Get the currently filtered data
        earthquakes = earthquake_cache["filtered_data"] or earthquake_cache["data"]
        
        # Get the hazard summary
        summary = get_seismic_hazard_summary(float(lat), float(lon), earthquakes)
        
        return jsonify(summary)
    except Exception as e:
        print(f"Error in hazard_summary: {str(e)}")
        return jsonify({"error": f"Failed to process request: {str(e)}"}), 500

@app.route('/api/report', methods=['POST', 'OPTIONS'])
def generate_earthquake_report():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
        
    try:
        data = request.json
        print(f"Received report request with data: {data}")
        
        # Required parameters
        lat = data.get('latitude')
        lon = data.get('longitude')
        radius = data.get('radius', 300)
        title = data.get('title', f"Earthquake Hazard Report ({datetime.now().strftime('%Y-%m-%d')})")
        
        # Handle time period or days
        days = data.get('days', 1)
        time_period = data.get('timePeriod')
        if time_period and not days:
            days_map = {
                'hour': 0.042,
                'day': 1,
                'week': 7,
                'month': 30
            }
            days = days_map.get(time_period, 1)
        
        # Handle min magnitude
        min_magnitude = data.get('minMagnitude', 1.0)
        
        # New parameter for analysis type
        analysis_type = data.get('analysisType', 'standard')
        
        if not lat or not lon:
            return jsonify({"error": "Latitude and longitude are required"}), 400
        
        # Get the currently filtered data or use default parameters
        if earthquake_cache["filtered_data"] is None:
            earthquakes = process_earthquake_data(
                earthquake_cache["data"],
                days_ago=float(days),
                min_magnitude=float(min_magnitude)
            )
        else:
            earthquakes = earthquake_cache["filtered_data"]
        
        # Perform analysis based on type
        if analysis_type == 'advanced':
            # Use OpenQuake analysis
            standard_analysis = perform_hazard_analysis(
                earthquakes, float(lat), float(lon), float(radius)
            )
            advanced_analysis = perform_openquake_hazard_analysis(
                float(lat), float(lon), earthquakes
            )
            # Combine analyses
            analysis_results = {
                **standard_analysis,
                'advanced_analysis': advanced_analysis
            }
        else:
            # Use standard analysis
            analysis_results = perform_hazard_analysis(
                earthquakes, float(lat), float(lon), float(radius)
            )
        
        # Generate PDF report
        pdf_path = generate_report(
            earthquakes, 
            analysis_results, 
            title, 
            float(lat), 
            float(lon), 
            float(radius),
            analysis_type=analysis_type
        )
        
        # Return PDF file
        return send_file(pdf_path, as_attachment=True, download_name="earthquake_report.pdf")
    except Exception as e:
        print(f"Error in generate_earthquake_report: {str(e)}")
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        return jsonify({
            "status": "online",
            "last_update": earthquake_cache["last_updated"].isoformat() if earthquake_cache["last_updated"] else None,
            "earthquake_count": len(earthquake_cache["data"]["features"]) if earthquake_cache["data"] else 0,
            "hazard_analysis_capabilities": [
                "standard",
                "advanced_openquake",
                "hazard_summary"
            ]
        })
    except Exception as e:
        print(f"Error in get_status: {str(e)}")
        return jsonify({"error": f"Failed to get status: {str(e)}"}), 500

if __name__ == '__main__':
    # Initialize data on startup
    try:
        print("Initializing earthquake data...")
        raw_data = fetch_earthquake_data()
        if raw_data:
            earthquake_cache["data"] = raw_data
            earthquake_cache["last_updated"] = datetime.now()
            print(f"Initial data loaded at {earthquake_cache['last_updated']}")
        else:
            print("Failed to load initial data")
    except Exception as e:
        print(f"Error loading initial data: {str(e)}")
    
    # Start Flask application
    app.run(debug=True, host='0.0.0.0', port=5000)