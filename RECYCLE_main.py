import numpy as np
import serial
import time
import subprocess
from PIL import Image
from tflite_runtime.interpreter import Interpreter

# Load TFLite model
interpreter = Interpreter(model_path="RECYCLE.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_shape = input_details[0]['shape'][1:3]  # (height, width)

# Serial connection
try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    time.sleep(2)
    print("Serial connected.")
except:
    ser = None
    print("Serial connection failed.")

print("Waiting for Arduino 'ready' signal...")

# Prediction stability
PREDICTION_REPEAT_THRESHOLD = 3
prediction_buffer = []
last_prediction = None

def get_stable_prediction(pred):
    global last_prediction, prediction_buffer
    if pred == last_prediction:
        prediction_buffer.append(pred)
    else:
        prediction_buffer = [pred]
        last_prediction = pred

    if len(prediction_buffer) >= PREDICTION_REPEAT_THRESHOLD:
        prediction_buffer = []
        return pred
    return None

def capture_image(image_path="capture.jpg"):
    # Use libcamera to capture a single image
    cmd = f"libcamera-still -o {image_path} --width {input_shape[1]} --height {input_shape[0]} --nopreview -t 1000"
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def load_image(path):
    img = Image.open(path).convert('RGB')
    img = np.array(img).astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)
    return img

# Main loop
while True:
    if ser and ser.in_waiting:
        msg = ser.readline().decode().strip()
        if msg.lower() == "ready":
            print("Trash detected — capturing image...")

            success = capture_image()
            if not success:
                print("Failed to capture image.")
                continue

            img = load_image("capture.jpg")

            interpreter.set_tensor(input_details[0]['index'], img)
            interpreter.invoke()
            output = interpreter.get_tensor(output_details[0]['index'])[0]
            predicted_class = int(np.argmax(output))

            print(f"Predicted: {predicted_class}")

            stable_result = get_stable_prediction(predicted_class)
            if stable_result is not None:
                print(f"Stable class: {stable_result}")
                if ser:
                    ser.write(f"{stable_result}\n".encode())
                    time.sleep(1)
            else:
                print("Waiting for stable prediction...")
