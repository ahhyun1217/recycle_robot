import cv2
import numpy as np
import time
import serial
from tflite_runtime.interpreter import Interpreter

# TFLite 모델 로딩
interpreter = Interpreter(model_path="RECYCLE.tflite")
interpreter.allocate_tensors()

# 입력 & 출력 정보
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# 카메라 초기화
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("카메라 열기 실패")
    exit()

# 입력 크기 (예: 224x224)
input_shape = input_details[0]['shape'][1:3]

# 🔌 시리얼 연결 (아두이노 연결 포트 확인 필요)
try:
    ser = serial.Serial('/dev/ttyUSB0', 9600)
except:
    ser = None
    print("시리얼 연결 실패 — USB 포트 확인")

print("분류 시작!")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # 전처리: 크기 조정, 정규화
    img = cv2.resize(frame, input_shape)
    img = np.expand_dims(img, axis=0)
    img = img.astype(np.float32) / 255.0

    # 추론
    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])[0]
    predicted_class = int(np.argmax(output))

    print("예측 클래스:", predicted_class)

    # 시리얼로 전송
    if ser:
        ser.write(f"{predicted_class}\n".encode())

    time.sleep(2)  # 처리 주기 조절
