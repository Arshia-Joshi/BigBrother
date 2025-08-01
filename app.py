from flask import Flask, render_template, Response, request
import cv2
import threading
import time
import os

app = Flask(__name__)
camera = cv2.VideoCapture(0)

recording = False
out = None

def gen_frames():
    global out, recording
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            if recording:
                out.write(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_recording')
def start_recording():
    global out, recording
    if not recording:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        os.makedirs('recordings', exist_ok=True)
        out = cv2.VideoWriter(f'recordings/{timestamp}.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (640, 480))
        recording = True
    return "Recording started"

@app.route('/stop_recording')
def stop_recording():
    global out, recording
    if recording:
        recording = False
        out.release()
    return "Recording stopped"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
