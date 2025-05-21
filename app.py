import subprocess
import os

def run_in_new_terminal_windows(path, command):
    abs_path = os.path.abspath(path)
    # Create the command to open a new cmd window, cd to the folder, and run the python command, keeping the window open
    cmd = f'start cmd /k "cd /d {abs_path} && {" ".join(command)}"'
    subprocess.Popen(cmd, shell=True)

# Run all your commands in separate terminals:
run_in_new_terminal_windows("earthquake_monitor/backend", ["python", "app.py"])
run_in_new_terminal_windows("earthquake_monitor/frontend", ["python", "-m", "http.server", "8000"])
run_in_new_terminal_windows("chatgptVersionFinal", ["python", "app.py"])
run_in_new_terminal_windows("weather_monitor/backend", ["python", "appweather.py"])
run_in_new_terminal_windows("FiresProjectNouamane", ["python", "server.py"])
