import json
import os
import shutil

import numpy as np
from PyQt6 import QtCore
from PyQt6.QtCore import QSize, QByteArray, QBuffer, QIODevice, Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel, QGraphicsBlurEffect, \
    QAbstractItemView, QSizePolicy, QHeaderView, QTableWidgetItem, QFileDialog, QButtonGroup;
from ui.login import Ui_LoginWindow
from ui.mainWindow import Ui_MainWindow

from PyQt6.QtGui import QMovie, QPixmap

import sys
sys.path.append("utils")

from utils.database_utils import *
from utils.sqls import *

from widgets import profile

from Threads.VideoCapture import VideoCaptureThread

import cv2 as cv

global user_id
user_id = 1

class loginWindow(QMainWindow):

    # 登陆成功信号
    loginSuccessSignal = QtCore.pyqtSignal()
    def __init__(self):
        super(loginWindow, self).__init__()
        self.ui = Ui_LoginWindow()
        self.ui.setupUi(self)
        # 隐藏框
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        # 登录
        self.ui.pushButton.clicked.connect(self.login)

    def login(self):
        self.ui.pushButton.setDisabled(True)
        QApplication.processEvents()
        username = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()
        if username == "" or password == "":
            self.ui.pushButton.setDisabled(False)
            QMessageBox.critical(self, '登录错误', '账号或密码不能为空')
            return
        result = sqlExecute(login_sql(username,md5(password)))
        if len(result) == 0:
            self.ui.pushButton.setDisabled(False)
            QMessageBox.critical(self, '登录错误', '账号或密码错误')
            self.ui.lineEdit.setText("")
            self.ui.lineEdit_2.setText("")
        else:
            user_id = result[0]
            self.loginSuccessSignal.emit()
            self.close()

    # 拖动窗口设置
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.geometry().contains(self.mapToGlobal(event.pos())):
            self.dis = self.mapToGlobal(event.pos()) - self.pos()
            self.dragging = True
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)  # 更改鼠标图标
    def mouseMoveEvent(self, mouse_event):
        if self.dragging:
            self.move(self.mapToGlobal(mouse_event.pos()) - self.dis)

    def mouseReleaseEvent(self, mouse_event):
        if mouse_event.button() == QtCore.Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        # self.setupUi(self)
        self.logon_window = loginWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.profile = profile.ProfileWindow()
        self.initbg()
        self.ui.pushButton_4.hide()
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        # self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.logon_window.loginSuccessSignal.connect(self.showMainWindow)
        self.ui.pushButton_5.clicked.connect(self.profile.show)
        self.switchingWindows()
        #初始化下拉框
        self.initComboBox()
        #初始化 教师 表
        self.initTeacherTable()
        #查找按钮实现条件查询
        self.ui.pushButton_9.clicked.connect(self.queryTeacher)
        #初始化 学院表
        self.initCollegeTable()
        #学院界面查找按钮实现条件查询
        self.ui.pushButton_11.clicked.connect(self.queryCollege)
        #根据编号回显表单数据
        self.ui.pushButton_15.clicked.connect(self.echoBack)
        #学院页修改按钮
        self.ui.pushButton_12.clicked.connect(self.updateCollege)
        #学院页删除按钮
        self.ui.pushButton_13.clicked.connect(self.deleteCollege)
        #学院页新增按钮
        self.ui.pushButton_14.clicked.connect(self.insertCollege)
        #初始化打开摄像头线程
        self.video_capture_thread = VideoCaptureThread()
        self.video_capture_thread.frame_ready.connect(self.update_frame)
        self.video_capture_thread.error_occurred.connect(self.show_error_message)
        self.video_capture_thread.camera_closed.connect(self.close_camera)
        self.video_capture_thread.set_avatar.connect(self.set_avatar)
        self.video_capture_thread.face_captured.connect(self.face_capture)
        self.face_id_name = {}
        # self.ui.label_22.setText(str(len(self.face_list)))
        #按钮初始化禁用
        self.button_disable()
        #单选框分组
        self.radio_button_group = QButtonGroup()
        self.radio_button_group.addButton(self.ui.radioButton)
        self.radio_button_group.addButton(self.ui.radioButton_2)
        # 创建LBPH人脸识别器
        # self.face_recognizer = cv.face.LBPHFaceRecognizer_create()
        # self.face_recognizer = cv.dnn.readNetFromONNX("resourses/dataset/faces/face_recognizer_fast.onnx")
        #创建人脸识别器
        self.face_recognizer = cv.FaceRecognizerSF.create('resourses/dataset/faces/face_recognition_sface_2021dec_int8.onnx','')
    def button_disable(self):
        self.ui.pushButton_19.setDisabled(True)
        self.ui.pushButton_20.setDisabled(True)
        self.ui.pushButton_21.setDisabled(True)

    def button_enable(self):
        self.ui.pushButton_19.setDisabled(False)
        self.ui.pushButton_20.setDisabled(False)
        self.ui.pushButton_21.setDisabled(False)

    def close_camera(self):
        self.ui.label_21.setText("摄像头已关闭")

    def show_error_message(self, error_message):
        QMessageBox.warning(self, '错误', error_message)

    # 人脸录入界面打开摄像头
    def on_pushButton_17_pressed(self):
        self.video_capture_thread.start()
        self.button_enable()


    #人脸录入界面关闭摄像头
    def on_pushButton_18_pressed(self):
        self.video_capture_thread.capture_running = False
        self.button_disable()

    #人脸录入界面设置图像按钮
    def on_pushButton_19_pressed(self):
        self.video_capture_thread.trigger_avatar_capture()

    def set_avatar(self,pixmap):
        pixmap = pixmap.scaled(self.ui.label_14.width(), self.ui.label_14.height())
        self.ui.label_14.setPixmap(pixmap)

    #人脸录入界面采集样本按钮
    def on_pushButton_20_pressed(self):
        id = self.ui.lineEdit_6.text()
        name = self.ui.lineEdit_7.text()
        if id is None or id.strip() == "":
            QMessageBox.warning(self, '编号错误', '编号不能为空')
            return
        if name is None or name.strip() == "":
            QMessageBox.warning(self, '姓名错误', '姓名不能为空')
            return
        with open("resourses/dataset/faces/id_name.json", "r") as file:
            self.face_id_name = json.load(file)
        if id not in self.face_id_name:
            self.face_id_name[id] = [name,[]]
        with open("resourses/dataset/faces/id_name.json", "w") as file:
            json.dump(self.face_id_name, file, ensure_ascii=False)
        index = self.get_next_index(id)
        filename = f"resourses/dataset/faces/{id}/face_{index}.png"
        self.video_capture_thread.face_capture(filename,id,name)
        self.ui.label_22.setText(str(index))

    def get_next_index(self,id):
        folder_path = f"resourses/dataset/faces/{id}"
        # 如果目录不存在，则返回0作为索引
        if not os.path.exists(folder_path):
            return 1
        # 获取目录下文件数量
        file_count = len(
            [name for name in os.listdir(folder_path)])
        return file_count + 1

    #人脸录入按钮
    def on_pushButton_21_pressed(self):
        # self.get_face_feature()
        # self.video_capture_thread.get_name_feature()
        self.video_capture_thread.reload_face_id_name()
    def get_face_feature(self):
        data_dir = "resourses/dataset/faces"
        faces = []
        labels = []

        for label in os.listdir(data_dir):
            label_dir = os.path.join(data_dir, label)
            if not os.path.isdir(label_dir):
                continue

            for image_name in os.listdir(label_dir):
                image_path = os.path.join(label_dir, image_name)
                image = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
                faces.append(image)
                labels.append(int(label))

        self.face_recognizer.alignCrop(faces)
        print('1')

    # def train_face_recognizer(self):
    #     data_dir = "resourses/dataset/faces"
    #     faces = []
    #     labels = []
    #
    #     for label in os.listdir(data_dir):
    #         label_dir = os.path.join(data_dir, label)
    #         if not os.path.isdir(label_dir):
    #             continue
    #
    #         for image_name in os.listdir(label_dir):
    #             image_path = os.path.join(label_dir, image_name)
    #             image = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
    #             faces.append(image)
    #             labels.append(int(label))
    #
    #     # # 创建LBPH人脸识别器
    #     # face_recognizer = cv.face.LBPHFaceRecognizer_create()
    #
    #     # 训练分类器
    #     self.face_recognizer.train(faces, np.array(labels))
    #
    #     # 保存分类器
    #     self.face_recognizer.save("resourses/dataset/faces/face_recognizer.xml")
    #
    #     print("人脸分类器已训练并保存为 face_recognizer.xml")

    # 人脸录入界面上传图片按钮
    def on_pushButton_22_pressed(self):
        file_path,_ = QFileDialog.getOpenFileName(self, "选择图片", "", "Image Files (*.png *.jpg *.bmp)")
        if file_path:
            pixmap = QPixmap(file_path)
            pixmap = pixmap.scaled(self.ui.label_14.width(), self.ui.label_14.height())
            self.ui.label_14.setPixmap(pixmap)
            self.ui.label_14.setScaledContents(True)

    # 回显教师信息
    def on_pushButton_16_pressed(self):
        teacher_id = self.ui.lineEdit_6.text()
        if teacher_id is None or teacher_id.strip() == "":
            QMessageBox.warning(self, '编号错误', '编号不能为空')
            return
        result = sqlExecute(query_teacher_byId_sql(teacher_id))[0]
        if len(result) == 0:
            QMessageBox.warning(self, '编号错误', '编号不存在')
            return
        result = result[0]
        self.ui.lineEdit_7.setText(result[0])  # 姓名
        if result[1] is not None:
            pixmap = QPixmap()
            pixmap.loadFromData(result[1])
            self.ui.label_14.setPixmap(pixmap)   #图片
        else:
            self.ui.label_14.setText("图片未找到")
        self.ui.comboBox_4.setCurrentText(result[2])   #职称
        if result[3] == '男':
            self.ui.radioButton.setChecked(True)
        else:
            self.ui.radioButton_2.setChecked(True)
        self.ui.lineEdit_8.setText(str(result[4]))    #年龄
        self.ui.lineEdit_9.setText(result[5])    #联系方式
        self.ui.comboBox_3.setCurrentText(result[6]) #所属学院
        self.ui.lineEdit_10.setText(result[7])    #研究领域

    # 人脸录入界面 修改按钮
    def on_pushButton_23_pressed(self):
        id = self.ui.lineEdit_6.text()
        if id is None or id.strip() == "":
            QMessageBox.warning(self, '编号错误', '编号不能为空')
            return
        result = sqlExecute(query_teacher_byId_sql(id))[0]
        if len(result) == 0:
            QMessageBox.warning(self, '编号错误', '编号不存在')
            return
        name = self.ui.lineEdit_7.text()
        photo = self.ui.label_14.pixmap()
        position = self.ui.comboBox_4.currentText()
        if self.ui.radioButton.isChecked():
            gender = '男'
        else:
            gender = '女'
        age = self.ui.lineEdit_8.text()
        phone = self.ui.lineEdit_9.text()
        college = self.ui.comboBox_3.currentText()
        research = self.ui.lineEdit_10.text()
        if name is None or name.strip() == "" or photo is None or \
                position is None or position.strip() == "" or age is None or age.strip() == "" or phone is None or \
                phone.strip() == "" or college is None or college.strip() == "" or research is None or \
                research.strip() == "":
            QMessageBox.warning(self, '信息错误', '信息不能为空')
            return
        photo_byte_array = QByteArray()
        buffer = QBuffer(photo_byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        photo.save(buffer, "PNG")
        buffer.close()
        college_id = sqlExecute(query_collegeId_byname_sql(college))[0][0][0]
        sql = "UPDATE teacher SET name = %s, position = %s, photo = %s, gender = %s, age = %s, phone = %s, department_id = %s, research_area = %s WHERE teacher_id = %s"
        values = (name, position, bytes(photo_byte_array), gender, age, phone, college_id, research, id)
        result, count = sqlExecute(sql, values)
        if count > 0:
            QMessageBox.information(self, '修改成功', '修改成功')
            self.initTeacherTable()

    # 人脸录入界面删除按钮
    def on_pushButton_24_pressed(self):
        id = self.ui.lineEdit_6.text()
        if id is None or id.strip() == "":
            QMessageBox.warning(self, '编号错误', '编号不能为空')
            return
        result = sqlExecute(query_teacher_byId_sql(id))[0]
        if len(result) == 0:
            QMessageBox.warning(self, '编号错误', '编号不存在')
            return
        dir_flag = False
        face_data_dir = f"resourses/dataset/faces/{id}"
        if os.path.exists(face_data_dir):
            shutil.rmtree(face_data_dir)
            dir_flag = True
        feature_flag = False
        with open("resourses/dataset/faces/id_name.json","r") as f:
            face_id_name = json.load(f)
        if id in face_id_name:
            del face_id_name[id]
            feature_flag = True
        with open("resourses/dataset/faces/id_name.json","w") as f:
            json.dump(face_id_name, f,ensure_ascii=False)
        count = 0
        if not os.path.exists(face_data_dir) or (dir_flag and feature_flag):
            result, count = sqlExecute(delete_teacher_byId_sql(id))

        if count > 0:
            QMessageBox.information(self, '删除成功', '删除成功')
            self.video_capture_thread.reload_face_id_name()

    # 人脸录入界面新增按钮
    def on_pushButton_25_pressed(self):
        id = self.ui.lineEdit_6.text()
        name = self.ui.lineEdit_7.text()
        photo = self.ui.label_14.pixmap()
        position = self.ui.comboBox_4.currentText()
        gender = ''
        if self.ui.radioButton.isChecked():
            gender = '男'
        else:
            gender = '女'
        age = self.ui.lineEdit_8.text()
        phone = self.ui.lineEdit_9.text()
        college = self.ui.comboBox_3.currentText()
        research = self.ui.lineEdit_10.text()
        if id is None or id.strip() == "" or name is None or name.strip() == "" or photo is None or \
                position is None or position.strip() == "" or age is None or age.strip() == "" or phone is None or \
                phone.strip() == "" or college is None or college.strip() == "" or research is None or \
                research.strip() == "":
            QMessageBox.warning(self, '信息错误', '教师信息不能为空')
            return
        result = sqlExecute(query_teacher_byId_sql(id))[0]
        if len(result) > 0:
            QMessageBox.warning(self, '编号错误', '编号已存在')
            return
        photo_byte_array = QByteArray()
        buffer = QBuffer(photo_byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        photo.save(buffer, "PNG")
        buffer.close()
        college_id = sqlExecute(query_collegeId_byname_sql(college))[0][0][0]
        sql = "INSERT INTO teacher(teacher_id, name, position, photo, gender, age, phone, department_id, research_area) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (id, name, position, bytes(photo_byte_array), gender, age, phone, college_id, research)
        result,count = sqlExecute(sql,values)
        if count > 0:
            QMessageBox.information(self, '新增成功', '新增成功')
            self.initTeacherTable()


    def face_capture(self,face):
        self.face_list.append(face)
        self.ui.label_22.setText(str(len(self.face_list)))


    def update_frame(self, pixmap):
        # pixmap = QPixmap.fromImage(q_img)
        self.ui.label_21.setPixmap(pixmap)


    def insertCollege(self):
        id = self.ui.lineEdit_3.text()
        if id is None or id.strip() == "":
            QMessageBox.warning(self, '编号错误', '新增编号为空')
            return
        result = sqlExecute(query_college_byId_sql(id))[0]
        if len(result) != 0:
            QMessageBox.warning(self, '编号错误', '新增编号已存在')
            return
        name = self.ui.lineEdit_4.text()
        introduction = self.ui.textEdit.toPlainText()
        website = self.ui.lineEdit_5.text()
        result,count = sqlExecute(insert_college_sql(id,name,introduction,website))
        if count > 0:
            QMessageBox.information(self, '新增成功', '新增成功')
            self.initCollegeTable()

    def deleteCollege(self):
        id = self.ui.lineEdit_3.text()
        if id is None or id.strip() == "":
            QMessageBox.warning(self, '编号错误', '删除编号为空')
            return
        result = sqlExecute(query_college_byId_sql(id))[0]
        if len(result) == 0:
            QMessageBox.warning(self, '编号错误', '删除编号不存在')
            return
        result,count = sqlExecute(delete_college_byId_sql(id))
        if count > 0:
            QMessageBox.information(self, '删除成功', '删除成功')
            self.initCollegeTable()

    def updateCollege(self):
        id = self.ui.lineEdit_3.text()
        if id is None or id.strip() == "":
            QMessageBox.warning(self, '编号错误', '修改编号为空')
            return
        result = sqlExecute(query_college_byId_sql(id))[0]
        if len(result) == 0:
            QMessageBox.warning(self, '编号错误', '修改编号不存在')
            return
        name = self.ui.lineEdit_4.text()
        introduction = self.ui.textEdit.toPlainText()
        website = self.ui.lineEdit_5.text()
        if name.strip() == "" or introduction.strip() == "" or website.strip() == "":
            QMessageBox.warning(self, '信息错误', '信息不能为空')
            return
        result, count = sqlExecute(update_college_byId_sql(id,name,introduction,website))
        if count > 0:
            QMessageBox.information(self, '修改成功', '修改成功')
            self.initCollegeTable()
    def echoBack(self):
        id = self.ui.lineEdit_3.text()
        if id is None or id.strip() == "":
            QMessageBox.warning(self, '编号错误', '编号为空')
            return
        result = sqlExecute(query_college_byId_sql(id))[0]
        if len(result) == 0:
            QMessageBox.warning(self, '编号错误', '编号不存在')
            return
        self.ui.lineEdit_4.setText(result[0][0])
        self.ui.lineEdit_5.setText(result[0][2])
        self.ui.textEdit.setText(result[0][1])

    def queryCollege(self):
        name = self.ui.lineEdit_2.text()
        condition = ""
        if name and name.strip() != "":
            condition += f" name LIKE '%{name}%'"
        # 最终的条件字符串
        if condition:
            condition = " WHERE" + condition
            self.initCollegeTable(condition)
            return
        self.initCollegeTable()

    def queryTeacher(self):
        name = self.ui.lineEdit.text()
        position = self.ui.comboBox.currentText()
        college = self.ui.comboBox_2.currentText()
        sql = f"select College_id from college where name = '{college}'"
        college_id = sqlExecute(sql)[0][0][0]
        condition = ""
        if name and name.strip() != "":
            condition += f" name LIKE '%{name}%'"

        if position and position.strip() != "":
            if condition:
                condition += " AND"
            condition += f" position = '{position}'"

        if college_id is not None:
            if condition:
                condition += " AND"
            condition += f" department_id = {college_id}"

        # 最终的条件字符串
        if condition:
            condition = " WHERE" + condition
            self.initTeacherTable(condition)



    def initComboBox(self):
        self.ui.comboBox_2.clear()
        result = sqlExecute(all_college_sql())[0]
        for i in result:
            self.ui.comboBox_2.addItem(i[0])
            self.ui.comboBox_3.addItem(i[0])
        self.ui.comboBox.setCurrentIndex(-1)
        self.ui.comboBox_2.setCurrentIndex(-1)
        self.ui.comboBox_3.setCurrentIndex(-1)
        self.ui.comboBox_4.setCurrentIndex(-1)


    def initTeacherTable(self,condition=None):

        result = sqlExecute(teacher_list_sql(condition))[0]
        row = 0
        if result is not None:
            row = len(result)
        self.ui.tableWidget.setColumnCount(6)
        self.ui.tableWidget.setRowCount(row)
        self.ui.tableWidget.verticalHeader().setVisible(False)
        self.ui.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ui.tableWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ui.tableWidget.setHorizontalHeaderLabels(["教师姓名", "照片", "职称", "性别", "所属学院", "研究领域"])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.tableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        for i in range(row):
            for j in range(6):
                if j == 1:  # 如果是图片列
                    # 从结果中读取 BLOB 数据
                    blob_data = result[i][j]
                    if blob_data is not None:
                        # 将 BLOB 数据转换为 QPixmap
                        pixmap = QPixmap()
                        pixmap.loadFromData(blob_data)

                        # 创建 QLabel，并将 QPixmap 显示在 QLabel 中
                        label = QLabel()
                        label.setPixmap(pixmap)
                        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                        # 调整 QPixmap 的大小以适应 QLabel
                        # label.setFixedSize(pixmap.size())
                        self.ui.tableWidget.setRowHeight(i, pixmap.height())

                        # 将 QLabel 插入到表格中
                        self.ui.tableWidget.setCellWidget(i, j, label)
                data = QTableWidgetItem(str(result[i][j]))
                self.ui.tableWidget.setItem(i, j, data)

    def initCollegeTable(self,condition=None):

        result = sqlExecute(college_list_sql(condition))[0]
        row = 0
        if result is not None:
            row = len(result)
        self.ui.tableWidget_2.setColumnCount(4)
        self.ui.tableWidget_2.setRowCount(row)
        self.ui.tableWidget_2.verticalHeader().setVisible(False)
        self.ui.tableWidget_2.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ui.tableWidget_2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ui.tableWidget_2.setHorizontalHeaderLabels(["编号","学院名称", "学院描述", "学院网址"])
        self.ui.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.tableWidget_2.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        for i in range(row):
            for j in range(4):
                data = QTableWidgetItem(str(result[i][j]))
                self.ui.tableWidget_2.setItem(i, j, data)


    def switchingWindows(self):
        self.ui.pushButton_6.clicked.connect(self.display_1)
        self.ui.pushButton_7.clicked.connect(self.display_4)
        self.ui.pushButton_10.clicked.connect(self.display_2)
        self.ui.pushButton_8.clicked.connect(self.display_3)

    def display_1(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def display_2(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def display_3(self):
        self.ui.stackedWidget.setCurrentIndex(3)

    def display_4(self):
        self.ui.stackedWidget.setCurrentIndex(2)


    def initbg(self):
        self.background_label = QLabel(self)
        # self.background_label.setGeometry(0,0,self.rect().width()-100,self.rect().height()-200)
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(2)
        self.background_label.setGraphicsEffect(blur_effect)
        self.movie = QMovie(":/images/images/bg2.gif")
        a= self.background_label.size()
        self.movie.setScaledSize(QSize(self.background_label.width(),self.background_label.height()))
        # self.background_label.setScaledContents(True)
        self.background_label.setMovie(self.movie)
        self.movie.start()

    def resizeEvent(self, event):
        self.background_label.setGeometry(0,0,self.rect().width(), self.rect().height())
        self.movie.setScaledSize(self.size())

    def showMainWindow(self):
        self.show()

    def showEvent(self, a0):
        self.background_label.lower()

        # 拖动窗口设置
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.geometry().contains(
                self.mapToGlobal(event.pos())):
            self.dis = self.mapToGlobal(event.pos()) - self.pos()
            self.dragging = True
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)  # 更改鼠标图标

    def mouseMoveEvent(self, mouse_event):
        if self.dragging:
            self.move(self.mapToGlobal(mouse_event.pos()) - self.dis)

    def mouseReleaseEvent(self, mouse_event):
        if mouse_event.button() == QtCore.Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())