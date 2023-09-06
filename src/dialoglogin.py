from PySide2 import QtWidgets, QtGui, QtCore
from Lib.bili_api.utils import cookieTools
from ui_dialoglogin import Ui_DialogLogin
from Lib.bili_api import user
from io import BytesIO
import qrcode
import pickle
import time

from utils import configUtils
from pprint import pprint


class DialogLogin(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_DialogLogin()
        self.ui.setupUi(self)

        self.load_thread = LoginDataThread(self)
        self.connect(
            self.load_thread,
            QtCore.SIGNAL("update_qrcode(QImage)"),
            self.update_qrcode,
        )
        self.connect(
            self.load_thread,
            QtCore.SIGNAL("update_status(QString)"),
            self.update_status,
        )
        self.connect(
            self.load_thread,
            QtCore.SIGNAL("finished()"),
            self.load_finished,
        )
        self.connect(
            self.load_thread,
            QtCore.SIGNAL("update_data(QByteArray)"),
            self.update_data,
        )
        self.load_thread.start()

    # Slot
    def update_qrcode(self, img: QtGui.QImage):
        self.ui.label_qrcode.setPixmap(QtGui.QPixmap.fromImage(img.scaled(500, 500)))

    # Slot
    def update_status(self, status: str):
        self.ui.label_status.setText(status)

    # Slot
    def update_data(self, data: QtCore.QByteArray):
        passport = pickle.loads(data.data())
        configUtils.setUserData("passport", passport)

    # Slot
    def load_finished(self):
        self.disconnect(self.load_thread)
        del self.load_thread
        self.close()


class LoginDataThread(QtCore.QThread):
    def __init__(self, parent: QtCore.QObject | None = ...) -> None:
        super().__init__(parent)

    def run(self):
        qr_info = user.get_login_url()
        qr = qrcode.make(qr_info["data"]["url"])
        img_buff = BytesIO()
        qr.save(img_buff, format="PNG")
        img_buff.seek(0)
        img = QtGui.QImage.fromData(img_buff.read())
        self.emit(
            QtCore.SIGNAL("update_qrcode(QImage)"),
            img,
        )
        self.emit(
            QtCore.SIGNAL("update_status(QString)"),
            "请扫描二维码登录",
        )
        login_status = False
        err_msg = ""
        with user.Get_login_info(qr_info["data"]["oauthKey"]) as getter:
            while not login_status:
                status = getter.request()
                if "code" in status:
                    if status["code"] != 0:
                        err_msg = "请求错误: " + status["message"]
                        break
                if str(status["data"]) == "-1":
                    err_msg = "密钥错误"
                    break
                elif str(status["data"]) == "-4":
                    self.emit(
                        QtCore.SIGNAL("update_status(QString)"), "请扫描二维码登录Bilibili"
                    )
                elif str(status["data"]) == "-5":
                    self.emit(QtCore.SIGNAL("update_status(QString)"), "扫描成功，请确认")
                elif status["status"]:
                    self.emit(QtCore.SIGNAL("update_status(QString)"), "登录成功")
                    login_status = True
                else:
                    err_msg = "二维码登录错误"
                    break
                time.sleep(1.2)
        if not login_status:
            self.emit(QtCore.SIGNAL("update_status(QString)"), err_msg)
            time.sleep(1)
            return
        cookie = cookieTools.get_cookie(status["data"]["url"])
        ret = {"ts": status["ts"], "data": cookie}
        ret = pickle.dumps(ret)
        ret = QtCore.QByteArray(ret)
        self.emit(QtCore.SIGNAL("update_data(QByteArray)"), ret)
        time.sleep(1)
