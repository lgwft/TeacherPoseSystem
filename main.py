from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QWidget,QMainWindow,QApplication;
from ui.login import Ui_LoginWindow
from ui.main import Ui_MainWindow
from resourses import resources_rc

import sys

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
        if self.ui.lineEdit.text() == 'admin' and self.ui.lineEdit_2.text() == '123456':
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


class MainWindow(QMainWindow,Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.logon_window = loginWindow()
        self.logon_window.loginSuccessSignal.connect(self.showMainWindow)

    def showMainWindow(self):
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.logon_window.show()

    sys.exit(app.exec())