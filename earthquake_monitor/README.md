# GlobalQuakeTracker

## Overview

GlobalQuakeTracker is a web-based earthquake monitoring system that provides real-time earthquake data visualization, analysis, and reporting. The application fetches earthquake data from the USGS API, processes it to perform hazard analysis, and generates interactive visualizations and detailed PDF reports.

## Features

- **Real-time Earthquake Data**: Automatically fetches and updates earthquake data from USGS
- **Interactive Map**: Visualize earthquakes on an interactive map with filtering options
- **Customizable Filtering**: Filter earthquakes by magnitude, time period, and region
- **Hazard Analysis**: Perform location-specific seismic hazard analysis
- **Detailed Reports**: Generate comprehensive PDF reports with analysis results and recommendations
- **Responsive Design**: Works on desktop and mobile devices

## Project Structure

```
earthquake_monitor/
├── backend/
│   ├── app.py                    # Main Flask application
│   ├── data_processor.py         # Process earthquake data
│   ├── hazard_analysis.py        # Mock OpenQuake hazard analysis
│   ├── report_generator.py       # PDF report generation
│   └── requirements.txt          # Backend dependencies
├── frontend/
│   ├── css/
│   │   └── style.css             # Custom styles
│   ├── js/
│   │   ├── chart.js              # Chart.js visualizations
│   │   ├── map.js                # Leaflet map functionality
│   │   └── app.js                # Main frontend application logic
│   └── index.html                # Main HTML page
└── README.md                     # Project documentation
```

## Installation

### Backend Setup

1. **Set up a Python environment**

   Make sure you have Python 3.8+ installed. Then create and activate a virtual environment:

   ```bash
   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies**

   Navigate to the backend directory and install the required packages:

   ```bash
   cd earthquake_monitor/backend
   pip install -r requirements.txt
   ```

3. **Run the Flask application**

   Start the Flask server:

   ```bash
   python app.py
   ```

   The server will start on http://0.0.0.0:5000 by default.

### Frontend Setup

1. **Set up a web server**

   You can use any web server to serve the frontend files. For development, you can use Python's built-in HTTP server:

   ```bash
   cd earthquake_monitor/frontend
   python -m http.server 8000
   ```

   This will serve the frontend on http://localhost:8000.

2. **Access the application**

   Open your web browser and navigate to http://localhost:8000 to access the GlobalQuakeTracker application.

## API Endpoints

The backend provides the following API endpoints:

1. **Get earthquake data**
   ```
   GET /api/earthquakes?days=7&magnitude=4.0
   ```
   - `days`: Number of days to look back (default: 7)
   - `magnitude`: Minimum magnitude to include (default: 4.0)

2. **Perform hazard analysis**
   ```
   POST /api/analysis
   ```
   Request body:
   ```json
   {
     "latitude": 37.7749,
     "longitude": -122.4194,
     "radius": 300
   }
   ```

3. **Generate a PDF report**
   ```
   POST /api/report
   ```
   Request body:
   ```json
   {
     "latitude": 37.7749,
     "longitude": -122.4194,
     "radius": 300,
     "title": "San Francisco Earthquake Hazard Report"
   }
   ```

4. **Check server status**
   ```
   GET /api/status
   ```

## Usage Guide

### Viewing Earthquake Data

1. Open the application in your web browser
2. The map will display recent earthquakes as circles (larger circles indicate higher magnitudes)
3. Use the filter controls to adjust:
   - Time period (1 day to 30 days)
   - Minimum magnitude
   - Geographic region (by dragging the map)

### Performing Hazard Analysis

1. Click on any location on the map or use the search function to select a location
2. Click the "Analyze" button to perform a hazard analysis for that location
3. View the analysis results including hazard level, key metrics, and nearby earthquakes

### Generating Reports

1. After performing an analysis, click the "Generate Report" button
2. Enter a title for your report if prompted
3. The application will generate and download a PDF report with detailed analysis and recommendations

## Troubleshooting

### Backend Issues

- **Server won't start**: Check if another process is using port 5000
- **Data not loading**: Ensure you have internet access for the USGS API
- **Dependencies error**: Verify all packages in requirements.txt are installed

### Frontend Issues

- **Map doesn't load**: Check your internet connection for loading map tiles
- **API errors**: Verify the backend server is running and accessible
- **Browser compatibility**: The application works best on modern browsers (Chrome, Firefox, Edge)

## Development

### Backend Development

The backend uses Flask and several Python libraries:
- `flask` and `flask-cors` for the API server
- `pandas` and `numpy` for data processing
- `requests` for API calls
- `reportlab` and `matplotlib` for PDF report generation

### Frontend Development

The frontend uses:
- Leaflet.js for the interactive map
- Chart.js for data visualizations
- Vanilla JavaScript for application logic
- CSS for styling

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- USGS Earthquake Hazards Program for providing real-time earthquake data
- Leaflet and Chart.js for the visualization libraries

NEZ
