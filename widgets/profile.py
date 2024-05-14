from PyQt6 import QtCore
from PyQt6.QtWidgets import QMainWindow, QWidget, QApplication, QMessageBox
import sys
from ui.profile import Ui_Form
from main import user_id
sys.path.append("utils")
from utils import sqls,database_utils
from resourses import resources_rc


class ProfileWindow(QWidget, Ui_Form):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        # self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setUserInfo(user_id)
        self.pushButton.clicked.connect(self.changeUserInfo)


    # 数据回显
    def setUserInfo(self,user_id):
        sql = sqls.queryAdmin_sql(user_id)
        result = database_utils.sqlExecute(sql)
        self.lineEdit.setText(result[0][0][1])
        self.lineEdit_2.setText(result[0][0][2])
        self.lineEdit_3.setText(result[0][0][2])
        self.label.setText(f"欢迎你，{result[0][0][1]}")

    # 修改用户信息
    def changeUserInfo(self):
        uname = self.lineEdit.text()
        pwd = self.lineEdit_2.text()
        pwd2 = self.lineEdit_3.text()
        if pwd != pwd2:
            QMessageBox.warning(self, '提示', '两次密码输入不一致')
        else:
            sql = sqls.change_password_sql(uname,pwd,user_id)
            result,count = database_utils.sqlExecute(sql)
            if count > 0:
                QMessageBox.information(self, '修改成功', '账号密码修改成功')
            else:
                QMessageBox.critical(self, '修改失败', '请联系管理员')

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
    window = ProfileWindow()
    window.show()
    sys.exit(app.exec())