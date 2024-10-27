import time
import socket
import pyaudio
import threading
import mediapipe as mp
from cv2 import rectangle, putText, flip, medianBlur, cvtColor, \
    VideoCapture, imshow, waitKey, destroyAllWindows, COLOR_BGR2RGB, FONT_HERSHEY_PLAIN

SERVER_HOST = 'SERVER-IP-ADDRESS'
SERVER_PORT = 5000

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 2048

faceDetected = False
faceDetectedTime = 0

audio_buffer = []
buffer_size = 5


def faceDetect():
    global faceDetected
    global faceDetectedTime
    faceDetection = mp.solutions.face_detection.FaceDetection(0.89)

    wCam, hCam = 1280, 720
    cap = VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)

    while True:
        raw_frame = cap.read()[1]
        frame = flip(raw_frame, 1)
        frame = medianBlur(frame, 3)
        rgbFrame = cvtColor(frame, COLOR_BGR2RGB)
        h, w, _ = frame.shape

        results = faceDetection.process(rgbFrame)
        noTarget = True
        if results.detections:
            for id_, detection in enumerate(results.detections):
                faceDetected = True
                faceDetectedTime = time.time()
                bbox = detection.location_data.relative_bounding_box
                xmin = int(bbox.xmin * w)
                ymin = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                top_left = (xmin, ymin)
                bottom_right = (xmin + width, ymin + height)

                rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
                putText(frame, "Face Acquired", (1000, 40),
                        FONT_HERSHEY_PLAIN, 2, (0, 0, 200), 2)
                noTarget = False
        if noTarget:
            if time.time() - faceDetectedTime > 1.5:
                faceDetected = False
                putText(frame, "No Face Detected", (1000, 40),
                        FONT_HERSHEY_PLAIN, 2, (0, 200, 200), 2)

        imshow("Home Automation", frame)

        if waitKey(1) == ord("d"):
            break

    cap.release()
    destroyAllWindows()


def main():
    global faceDetected
    global audio_buffer
    global buffer_size

    print("Connecting")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, output=True, frames_per_buffer=CHUNK)

    print("Connected to the server. Start receiving audio...")

    try:
        while True:
            data = client_socket.recv(CHUNK)
            if faceDetected:
                audio_buffer.append(data)
                if not data:
                    break
                if len(audio_buffer) > buffer_size:
                    stream.write(data)
            if not data:
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing connection...")
        stream.stop_stream()
        stream.close()
        audio.terminate()
        client_socket.close()


if __name__ == '__main__':

    print("Initializing Face Detection")
    faceDetectThread = threading.Thread(target=faceDetect)
    faceDetectThread.start()
    try:
        main()
    finally:
        faceDetectThread.join()
        print("Ambientation node stopped")
