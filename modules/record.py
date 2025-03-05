import subprocess
import os
import sys
import threading
import re

def list_devices():
    cmd = ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy']
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
    video_devices, audio_devices = [], []
    for line in process.stderr:
        match = re.search(r'\[dshow @ .*\] "(.*)"', line)
        if match:
            device_name = match.group(1)
            if "video" in line.lower():
                video_devices.append(device_name)
            elif "audio" in line.lower():
                audio_devices.append(device_name)
    return video_devices, audio_devices

def start_recording(video_device, audio_device, output_filename="output.mkv"):
    if os.path.exists(output_filename):
        os.remove(output_filename)
    command = [
        "ffmpeg", "-f", "dshow", "-rtbufsize", "100M",
        "-i", f"video={video_device}:audio={audio_device}",
        "-pix_fmt", "yuv420p", "-s", "640x480", "-r", "25",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-b:v", "1M",
        "-c:a", "aac", "-b:a", "128k", "-map", "0:v", "-map", "0:a",
        output_filename
    ]
    # Start ffmpeg process without blocking
    process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)

    # Function to check for 'q' input
    def check_for_quit():
        while True:
            if input("Press 'q' to quit: ").lower() == 'q':
                process.terminate()  # Gently stop ffmpeg
                print("Recording stopped.")
                break

    # Run the quit check in a separate thread so it doesn’t block
    quit_thread = threading.Thread(target=check_for_quit)
    quit_thread.start()

    # Wait for ffmpeg to finish (either naturally or via terminate)
    process.wait()

# Example usage
if __name__ == "__main__":
    video_devices, audio_devices = list_devices()
    if video_devices and audio_devices:
        start_recording(video_devices[0], audio_devices[0])
    else:
        print("No devices found.")