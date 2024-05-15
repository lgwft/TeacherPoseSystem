import codecs
import json
import os.path

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
import types

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
        # 初始化人脸检测器
        self.face_detector = cv2.FaceDetectorYN.create(
            model="resourses/face_detector/face_detection_yunet_2023mar_int8.onnx", config='', input_size=(480, 640))   #input_size为摄像头frame尺寸
        # 初始化人脸识别器
        self.face_recongnizer = cv2.FaceRecognizerSF.create(
            model="resourses/dataset/faces/face_recognition_sface_2021dec_int8.onnx", config='')
        # 加载人脸检测器 haar特征级联检测器
        # self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # self.face_detect_net = cv2.dnn.readNetFromCaffe("resourses/face_detector/deploy.prototxt.txt", "resourses/face_detector/res10_300x300_ssd_iter_140000.caffemodel")
        # self.face_recognition = cv2.face.LBPHFaceRecognizer_create()
        # self.face_recognition.read("resourses/dataset/faces/face_recognizer.xml")
        # self.face_id_name = json.load(open("resourses/dataset/faces/id_name.json", "r"))
        self.id_name= json.load(open("resourses/dataset/faces/id_name.json", "r"))
        # self.name_features = self.get_name_feature()
        self.THRESHOLD = 8  # 识别阈值


    def reload_face_id_name(self):
       with codecs.open("resourses/dataset/faces/id_name.json", "r") as f:
            self.id_name= json.load(f)


    def detect_faces_net(self, frame):
        self.face_detector.setInputSize((frame.shape[1], frame.shape[0]))
        self.face_detector.setScoreThreshold(0.7)
        self.face_detector.setNMSThreshold(0.3)
        self.face_detector.setTopK(2)
        faces = self.face_detector.detect(frame)[1]

        return faces

    def draw_faces(self, frame, faces):
        for face in faces:
            # 解析人脸数据
            face_box = face[:4]
            right_eye = face[4:6]
            left_eye = face[6:8]
            nose = face[8:10]
            right_mouth = face[10:12]
            left_mouth = face[12:14]
            confidence = face[14]

            # 绘制人脸框
            x, y, w, h = [int(coord) for coord in face_box]   # 将坐标转换为整数
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            #绘制关键点
            for point in [right_eye, left_eye, nose, right_mouth, left_mouth]:
                cv2.circle(frame, (int(point[0]), int(point[1])), 2, (0, 255, 255), -1)

            # 显示置信度
            # cv2.putText(frame, f'Confidence: {confidence}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
            #             cv2.LINE_AA)
        return frame

    def face_align(self, frame,faces):
        faces_aligned = []
        for face in faces:
            face_align = self.face_recongnizer.alignCrop(frame, face)
            faces_aligned.append(face_align)
        return faces_aligned

    def face_recognition(self, faces_aligned):
        faces_feature = []
        for face in faces_aligned:
            face_feature = self.face_recongnizer.feature(face)
            faces_feature.append(face_feature)
        return faces_feature


    def recongnition_face(self, faces_feature):
        recognized_names = []
        for face_feature in faces_feature:
            min_distance = float('inf')
            recognized_name = "Unknown"

            for id, (name, features) in self.id_name.items():
                for feature in features:
                    distance = np.linalg.norm(face_feature - np.array(feature))
                    if distance < min_distance:
                        min_distance = distance
                        recognized_name = name

            # 如果最小距离小于阈值，则认为识别成功
            if min_distance < self.THRESHOLD:
                recognized_names.append(recognized_name)
            else:
                recognized_names.append("Unknown")

        return recognized_names


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
                self.current_frame = frame.copy()
                if not ret:
                    break
                faces = self.detect_faces_net(frame)
                self.current_faces = faces
                if faces is not None:
                    frame = self.draw_faces(frame, faces)
                    if len(faces) < 2:
                        faces_aligned = self.face_align(frame, faces)
                        feaces_feature = self.face_recognition(faces_aligned)
                        name = self.recongnition_face(feaces_feature)[0]
                        #绘制名字----------⬇
                        face_box = faces[0][:4]
                        x, y, w, h = [int(coord) for coord in face_box]  # 将坐标转换为整数
                        frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        draw = ImageDraw.Draw(frame)
                        fontStyle = ImageFont.truetype("resourses/font/simhei.ttf", 20)
                        draw.text((x, y - 20), name, font=fontStyle, fill=(0, 255, 0))
                        frame = cv2.cvtColor(np.asarray(frame), cv2.COLOR_RGB2BGR)
                        #----------------⬆
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


    def face_capture(self,filename,id,name):
        frame = self.current_frame
        faces = self.current_faces
        if faces is not None and len(faces) < 2:
            faces_align = self.face_recongnizer.alignCrop(frame, faces)
            faces_feature = self.face_recongnizer.feature(faces_align)
            faces_feature = faces_feature.tolist()
            with open("resourses/dataset/faces/id_name.json","r") as file:
                self.face_id_name = json.load(file)
            dict = self.face_id_name[id][1]
            dict.append(faces_feature)
            with open("resourses/dataset/faces/id_name.json", "w") as file:
                json.dump(self.face_id_name, file, ensure_ascii=False)
            for face in faces:
                face_box = face[:4]
                x, y, w, h = [int(coord) for coord in face_box]
                face_img = frame[y:y + h, x:x + w]
                print(face_img.shape)
                dirname = os.path.dirname(filename)
                os.makedirs(dirname, exist_ok=True)
                if w!=0 and h!=0:
                    bool= cv2.imwrite(filename, face_img)
                    print(bool)

    def reload_face_recognizer(self):
        self.face_recognition.read("resourses/dataset/faces/face_recognizer.xml")

