from flask import Flask, render_template, jsonify
import os
import subprocess

app = Flask(__name__)

# Store subprocesses so we can terminate them if needed
monitor_processes = []

def start_monitoring_systems():
    """Start all monitoring systems as separate processes"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    try:
        # Start Weather Monitor
        weather_dir = os.path.join(project_root, 'weather_monitor', 'backend')
        weather_proc = subprocess.Popen(['python3', 'appweather.py'], cwd=weather_dir)
        monitor_processes.append(weather_proc)
        print("Weather Monitor started on port 5001")

        # Start Fire Monitor
        fire_dir = os.path.join(project_root, 'Fire_monitor')
        fire_proc = subprocess.Popen(['python3', 'server.py'], cwd=fire_dir)
        monitor_processes.append(fire_proc)
        print("Fire Monitor started on port 5002")

        # Start Earthquake Monitor
        eq_dir = project_root
        eq_proc = subprocess.Popen(['python3', '-m', 'earthquake_monitor.backend.app'], cwd=eq_dir)
        monitor_processes.append(eq_proc)
        print("Earthquake Monitor started on port 5003")

    except Exception as e:
        print(f"Error starting monitoring systems: {str(e)}")
        raise

@app.route('/')
def welcome():
    """Serve the welcome page"""
    return render_template('welcome.html')

@app.route('/health')
def health_check():
    """Dummy health check (sub-apps run separately)"""
    return jsonify({'status': 'healthy'})

def open_browser():
    import webbrowser, time
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Move welcome.html to templates directory
    if os.path.exists('welcome.html'):
        os.rename('welcome.html', 'templates/welcome.html')
    
    # Start all monitoring systems as subprocesses
    start_monitoring_systems()
    
    # Open browser in a separate thread
    from threading import Thread
    Thread(target=open_browser).start()
    
    # Start Flask server
    app.run(debug=True) 