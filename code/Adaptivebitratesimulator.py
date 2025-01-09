import psutil
import time
import cv2
import subprocess
import threading
from tkinter import Tk,Label,Button,StringVar
import PyQt5
from PyQt5.QtCore import QLibraryInfo

import os
import sys

if getattr(sys, 'frozen', False):
    # If running as a bundled executable
    base_path = sys._MEIPASS
else:
    # If running as a script
    base_path = os.path.dirname(os.path.abspath(__file__))

# Dynamically resolve paths for the video and plugins
video_path = os.path.join(base_path, "Videos", "TOS_1080p.mp4")
plugins_path = os.path.join(base_path, "PyQt5", "Qt5", "plugins")
os.environ["QT_PLUGIN_PATH"] = plugins_path

#Global variables
bandwidth_values = []
simulation_running = False
cap = None # Video capture object
buffer = [] # Simulated buffer
buffer_lock = threading.Lock()
ffplay_process = None # Audio playback process
current_resolution = (1920,1080) # Default resolution

# File path to high-resolution video
video_path = r"C:\Users\Anagha\OneDrive\Desktop\AdaptiveBitRateOptimization\Videos\TOS_1080p.mp4"

# Resolution thresholds (width, height, bandwidth in kbps)
resolution_options = [
    (1920,1080,5000), #1080p
    (1280,720,2500),  #720p
    (854, 480, 1000), #480p
    (640,360,500),    #360p
    (426, 240, 200),  #240p
    (256, 144,50),    #144p
]

#GUI variables
app = Tk()
app.title("Adaptive Video Player")
app.geometry("400x200")
current_bandwidth_display = StringVar(value="Bandwidth: Calculating...")
current_resolution_display = StringVar(value="Resolution: Waiting...")

def get_optimal_resolution(bandwidth):
    """
    Determine the optimal resolution based on current bandwidth.
    """
    for width, height, threshold in resolution_options:
        if bandwidth >= threshold:
            return(width,height)
        return(256,144) # Lowest resolution

def play_audio():
    """
    Play audio using ffplay in a separate process.
    """
    global ffplay_process
    stop_audio() #Stop any currently playing audio
    ffplay_process = subprocess.Popen(["ffplay","-nodisp","-autoexit",video_path], stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def stop_audio():
    """
    Stop any currently playing audio.
    """
    global ffplay_process
    if ffplay_process:
        ffplay_process.terminate()
        ffplay_process = None

def capture_real_bandwidth():
    """Simulate real-time network bandwidth monitoring."""
    global bandwidth_values,simulation_running
    previous_stats = psutil.net_io_counters()

    while simulation_running:
        current_stats = psutil.net_io_counters()
        bytes_sent = current_stats.bytes_sent - previous_stats.bytes_sent
        bytes_received = current_stats.bytes_recv - previous_stats.bytes_recv
        previous_stats = current_stats

        bandwidth_kbps = (bytes_sent+bytes_received) * 8/1000
        bandwidth_values.append(bandwidth_kbps)
        current_bandwidth_display.set(f"Bandwidth: {bandwidth_kbps:.2f} kbps")

def load_video_to_buffer():
    """Simulate buffering by reading video frames and resizing dynamically"""
    global cap, buffer,simulation_running,current_resolution
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Failed to open video file.")
        simulation_running = False
        return
    while simulation_running:
        with buffer_lock:
            if len(buffer) < 100: #Buffer size limit
                ret,frame = cap.read()
                if not ret:
                    break
                resized_frame = cv2.resize(frame, current_resolution)
                buffer.append(resized_frame)
        time.sleep(0.01) #Simulate buffering delay

    cap.release()

def play_video_from_buffer():
    """Play video frames from the simulated buffer"""
    global buffer, simulation_running, current_resolution
    play_audio()
    while simulation_running:
        with buffer_lock:
            if buffer:
                frame = buffer.pop(0)
                cv2.imshow("Video Player", frame)
                if cv2.waitKey(15) & 0xFF == ord("q"):
                    simulation_running = False
                    break
        # Adjust resolution dynamically based on bandwidth
        if bandwidth_values:
            current_bandwidth = bandwidth_values[-1]
            optimal_resolution = get_optimal_resolution(current_bandwidth)
            if optimal_resolution!=current_resolution:
                current_resolution = optimal_resolution
                current_resolution_display.set(f"Resolution: {current_resolution[1]}p")
    cv2.destroyAllWindows()
    stop_audio() # Stop audio playback


def start_simulation():
    """
    Start the adaptive video playback simulation.
    """
    global simulation_running, buffer, bandwidth_values
    if simulation_running:
        return
    simulation_running = True
    buffer.clear()
    bandwidth_values.clear()

    threading.Thread(target=capture_real_bandwidth, daemon=True).start()
    threading.Thread(target=load_video_to_buffer, daemon=True).start()
    threading.Thread(target=play_video_from_buffer, daemon=True).start()

def stop_simulation():
    """
    Stop the adaptive video playback simulation.
    """
    global simulation_running
    simulation_running = False
    cv2.destroyAllWindows()
    stop_audio()

# GUI Elements
Label(app, text="Adaptive Video Player", font=("Arial", 16)).pack(pady=10)
Label(app, textvariable=current_bandwidth_display, font=("Arial", 12)).pack()
Label(app, textvariable=current_resolution_display, font=("Arial", 12)).pack()
Button(app, text="Start Playback", command=start_simulation, width=20).pack(pady=10)
Button(app, text="Stop Playback", command=stop_simulation, width=20).pack()

app.mainloop()






