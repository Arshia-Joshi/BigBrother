from flask import Flask, render_template, Response
from picamera2 import Picamera2
import threading
import time
import cv2
import os

app = Flask(__name__)
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(video_config)
picam2.start()

frame = None
recording = False
writer = None
frame_lock = threading.Lock()

def grab_frames():
    global frame, writer, recording
    while True:
        img = picam2.capture_array()
        with frame_lock:
            frame = img
            if recording and writer:
                writer.write(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

threading.Thread(target=grab_frames, daemon=True).start()

def generate():
    global frame
    while True:
        with frame_lock:
            if frame is None:
                continue
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_recording')
def start_recording():
    global writer, recording
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs("recordings", exist_ok=True)
    filepath = f"recordings/{timestamp}.mp4"
    writer = cv2.VideoWriter(filepath, cv2.VideoWriter_fourcc(*'mp4v'), 20, (640, 480))
    recording = True
    return "Recording started"

@app.route('/stop_recording')
def stop_recording():
    global writer, recording
    if writer:
        recording = False
        writer.release()
        writer = None
    return "Recording stopped"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
