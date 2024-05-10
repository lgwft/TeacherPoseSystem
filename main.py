from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QWidget, QMainWindow, QApplication, QMessageBox,QLabel,QGraphicsBlurEffect;
from ui.login import Ui_LoginWindow
from ui.mainWindow import Ui_MainWindow
from resourses import resources_rc

from PyQt6.QtGui import QMovie

import sys
sys.path.append("utils")

from utils.database_utils import *
from utils.sqls import *



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
        # self.show()

    def login(self):
        self.ui.pushButton.setDisabled(True)
        QApplication.processEvents()
        username = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()
        if username == "" or password == "":
            self.ui.pushButton.setDisabled(False)
            QMessageBox.critical(self, '登录错误', '账号或密码不能为空')
            return
        result = sqlExecute(login_sql(username,password))
        if len(result) == 0:
            self.ui.pushButton.setDisabled(False)
            QMessageBox.critical(self, '登录错误', '账号或密码错误')
            self.ui.lineEdit.setText("")
            self.ui.lineEdit_2.setText("")
        else:
            self.loginSuccessSignal.emit()
            self.close()
        # if self.ui.lineEdit.text() == 'admin' and self.ui.lineEdit_2.text() == '123456':
        #     self.loginSuccessSignal.emit()
        #     self.close()

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
        self.initbg()
        self.logon_window.loginSuccessSignal.connect(self.showMainWindow)

    def initbg(self):
        self.background_label = QLabel(self)
        self.background_label.setGeometry(self.rect())
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(20)
        self.background_label.setGraphicsEffect(blur_effect)
        self.movie = QMovie(":/images/images/bg.gif")
        self.movie.setScaledSize(self.background_label.size())
        self.background_label.setScaledContents(True)
        self.background_label.setMovie(self.movie)
        self.movie.start()

    def resizeEvent(self, event):
        self.background_label.setGeometry(self.rect())
        self.movie.setScaledSize(self.size())

    def showMainWindow(self):
        self.show()

    def showEvent(self, a0):
        self.background_label.lower()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())