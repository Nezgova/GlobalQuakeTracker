from flask import Flask, jsonify, request, send_from_directory
from predictions.fire_predictor import predict_fires
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__, static_folder='.')

# Configuration
DEFAULT_LAT = 12.3
DEFAULT_LON = 34.5
DEFAULT_HOURS = 24

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory('js', path)

@app.route('/api/fires')
def get_fires():
    try:
        # Récupération des paramètres de requête
        lat = float(request.args.get('lat', DEFAULT_LAT))
        lon = float(request.args.get('lon', DEFAULT_LON))
        hours = int(request.args.get('hours', DEFAULT_HOURS))
        
        # Génération des prédictions
        fires = predict_fires(lat, lon, hours)
        
        # Conversion des données pour l'API
        fire_data = []
        for fire in fires:
            fire_data.append({
                'lat': fire['lat'],
                'lon': fire['lon'],
                'intensity': fire['intensity'],
                'time': fire['time'].isoformat()
            })
        
        return jsonify(fire_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        fires = data.get('fires', [])
        filters = data.get('filters', {})
        
        # Ici, vous pouvez implémenter la génération du rapport PDF
        # Pour l'instant, nous retournons un message de succès
        return jsonify({
            'message': 'Rapport généré avec succès',
            'filters': filters,
            'fire_count': len(fires)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5004) 