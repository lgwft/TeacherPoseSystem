import codecs
import json
import os.path

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox

from PIL import Image, ImageDraw, ImageFont


class VideoCaptureThread(QThread):
    frame_ready = pyqtSignal(QPixmap)
    set_avatar = pyqtSignal(QPixmap)
    error_occurred = pyqtSignal(str)
    camera_closed = pyqtSignal()
    face_captured = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        # 摄像头是否运行
        self.capture_running = False
        # 加载人脸检测器 haar特征级联检测器
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_detect_net = cv2.dnn.readNetFromCaffe("resourses/face_detector/deploy.prototxt.txt", "resourses/face_detector/res10_300x300_ssd_iter_140000.caffemodel")
        self.face_recognition = cv2.face.LBPHFaceRecognizer_create()
        self.face_recognition.read("resourses/dataset/faces/face_recognizer.xml")
        self.face_id_name = json.load(open("resourses/dataset/faces/id_name.json", "r"))

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        return faces

    def detect_faces_net(self, frame):
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        self.face_detect_net.setInput(blob)
        detections = self.face_detect_net.forward()

        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:  # Only consider detections with confidence greater than 0.5
                box = detections[0, 0, i, 3:7] * np.array(
                    [frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])
                (startX, startY, endX, endY) = box.astype("int")
                faces.append((startX, startY, endX - startX, endY - startY))

        return faces

    def run(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.capture_running = False
            self.error_occurred.emit('摄像头打开失败，请检查连接')
            return

        self.capture_running = True
        try:
            while self.capture_running:
                ret, frame = self.cap.read()
                if not ret:
                    break
                # haar检测人脸代码块-------------↓
                # faces = self.detect_faces(frame)
                # if len(faces) > 0:
                #     for (x, y, w, h) in faces:
                #         cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # ------------------------↑
                # dnn检测人脸代码块-------------↓
                faces = self.detect_faces_net(frame)
                if len(faces) > 0:
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        # 人脸识别模块
                        ids,confidence = self.face_recognition.predict(cv2.cvtColor(frame[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY))
                        if confidence < 50:
                            name = "Unknown"
                        else:
                            name = self.face_id_name[str(ids)]
                        frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        draw = ImageDraw.Draw(frame)
                        fontStyle = ImageFont.truetype("resourses/font/simhei.ttf", 20)
                        draw.text((x, y-20), name, font=fontStyle, fill=(0, 255, 0))
                        frame = cv2.cvtColor(np.asarray(frame), cv2.COLOR_RGB2BGR)
                        # cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                # ------------------------↑
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将图像从 BGR 转换为 RGB
                h, w, ch = img.shape
                bytes_per_line = ch * w
                q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)
                if pixmap.width() > 570 :
                    ratio = pixmap.width() / 570
                    pixmap.setDevicePixelRatio(ratio)
                self.frame_ready.emit(pixmap)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.cap.release()
        if self.capture_running is False:
            self.camera_closed.emit()

    def trigger_avatar_capture(self):
        ret, frame = self.cap.read()
        if ret:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = img.shape
            bytes_per_line = ch * w
            q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            self.set_avatar.emit(pixmap)

    def face_capture(self,filename):
        ret, frame = self.cap.read()
        if ret:
            # gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_img = self.detect_faces_net(frame)
            if len(face_img) > 0:
                x, y, w, h = face_img[0]
                face_img = frame[y:y + h, x:x + w]
                print(face_img.shape)
                # face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                dirname = os.path.dirname(filename)
                os.makedirs(dirname, exist_ok=True)
                bool = cv2.imwrite(filename, face_img)
                print(bool)
                # self.face_captured.emit(face_img_rgb)

    def reload_face_recognizer(self):
        self.face_recognition.read("resourses/dataset/faces/face_recognizer.xml")

