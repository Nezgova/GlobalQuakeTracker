from flask import Flask, render_template
import threading
import subprocess
import sys
import os


app = Flask(__name__)

@app.route('/')
def welcome():
    return render_template('welcome.html')

# Function to run a backend server
def run_backend(script_path, port):
    subprocess.run([sys.executable, script_path], env=dict(os.environ, FLASK_RUN_PORT=str(port)))

# Start backend servers in separate threads
weather_thread = threading.Thread(target=run_backend, args=('weather_monitor/backend/appweather.py', 5001))
fire_thread = threading.Thread(target=run_backend, args=('FiresProjectNouamane/server.py', 5002))
earthquake_thread = threading.Thread(target=run_backend, args=('earthquake_monitor/backend/app.py', 5003))
chatbot_thread = threading.Thread(target=run_backend, args=('chatgptVersionFinal/app.py', 5004))

weather_thread.start()
fire_thread.start()
earthquake_thread.start()
chatbot_thread.start()

if __name__ == '__main__':
    app.run(port=5000, debug=False) 
