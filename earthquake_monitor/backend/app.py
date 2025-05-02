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
from hazard_analysis import perform_hazard_analysis
from report_generator import generate_report

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
    # Query parameters
    days = int(request.args.get('days', 7))  # Default to 7 days
    min_magnitude = float(request.args.get('magnitude', 4.0))  # Default to magnitude 4.0+
    
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

@app.route('/api/analysis', methods=['POST'])
def analyze_earthquakes():
    data = request.json
    
    # Extract parameters
    lat = data.get('latitude')
    lon = data.get('longitude')
    radius = data.get('radius', 300)  # Default 300km radius
    
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
    
    # Perform hazard analysis
    analysis_results = perform_hazard_analysis(earthquakes, float(lat), float(lon), float(radius))
    
    return jsonify(analysis_results)

@app.route('/api/report', methods=['POST'])
def generate_earthquake_report():
    data = request.json
    
    # Required parameters
    lat = data.get('latitude')
    lon = data.get('longitude')
    radius = data.get('radius', 300)
    title = data.get('title', f"Earthquake Hazard Report ({datetime.now().strftime('%Y-%m-%d')})")
    
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
    
    # Perform analysis
    analysis_results = perform_hazard_analysis(earthquakes, float(lat), float(lon), float(radius))
    
    # Generate PDF report
    pdf_path = generate_report(earthquakes, analysis_results, title, float(lat), float(lon), float(radius))
    
    # Return PDF file
    return send_file(pdf_path, as_attachment=True, download_name="earthquake_report.pdf")

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": "online",
        "last_update": earthquake_cache["last_updated"].isoformat() if earthquake_cache["last_updated"] else None,
        "earthquake_count": len(earthquake_cache["data"]["features"]) if earthquake_cache["data"] else 0
    })

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