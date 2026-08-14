import pickle
import time
from io import BytesIO

import qrcode
from PySide2 import QtWidgets, QtGui, QtCore

from Lib.bili_api import user
from Lib.bili_api.utils import cookieTools, passport
from ui_dialoglogin import Ui_DialogLogin
from utils import configUtils


class DialogLogin(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget, userdata: configUtils.UserDataHelper) -> None:
        super().__init__(parent)
        self.ui = Ui_DialogLogin()
        self.ui.setupUi(self)
        self.userdata = userdata
        self.dialog_end = False

        self.load_thread = LoginDataThread(self)
        self.load_thread.update_qrcode.connect(self.update_qrcode)
        self.load_thread.update_status.connect(self.update_status)
        self.load_thread.finished.connect(self.load_finished)
        self.load_thread.update_data.connect(self.update_data)
        self.finished.connect(self.dialog_finished)
        self.load_thread.start()

    @QtCore.Slot(QtGui.QImage)
    def update_qrcode(self, img: QtGui.QImage):
        self.ui.label_qrcode.setPixmap(QtGui.QPixmap.fromImage(img.scaled(500, 500)))

    @QtCore.Slot(str)
    def update_status(self, status: str):
        self.ui.label_status.setText(status)

    @QtCore.Slot(QtCore.QByteArray, str)
    def update_data(self, data: QtCore.QByteArray, key: str):
        passp = pickle.loads(data.data())
        self.userdata.set(self.userdata.CFGS.PASSPORT, passp)
        self.userdata.set(self.userdata.CFGS.PASSPORT_CRYPT_KEY, key)
        self.userdata.save()

    @QtCore.Slot()
    def load_finished(self):
        self.disconnect(self.load_thread)
        self.close()

    @QtCore.Slot(int)
    def dialog_finished(self, _result: int):
        self.dialog_end = True
        while not self.load_thread.thread_finished:
            pass


class LoginDataThread(QtCore.QThread):
    update_qrcode = QtCore.Signal(QtGui.QImage)
    update_status = QtCore.Signal(str)
    update_data = QtCore.Signal(QtCore.QByteArray, str)

    def __init__(self, parent: QtCore.QObject = ...) -> None:
        super().__init__(parent)
        self.thread_finished = False

    def self_finished(self):
        self.thread_finished = True

    def run(self):
        qr_info = user.get_login_url()
        qr = qrcode.make(qr_info["data"]["url"])
        img_buff = BytesIO()
        qr.save(img_buff, format="PNG")
        img_buff.seek(0)
        img = QtGui.QImage.fromData(img_buff.read())
        self.update_qrcode.emit(img)
        self.update_status.emit("请扫描二维码登录")
        login_status = False
        err_msg = ""
        headers = None
        try:
            with user.Get_login_info(qr_info["data"]["qrcode_key"]) as getter:
                while not login_status and not self.parent().dialog_end:
                    status = getter.request()
                    if self.parent().dialog_end:
                        break
                    if "code" in status:
                        if status["code"] != 0:
                            err_msg = "请求错误: " + status["message"]
                            break
                    if str(status["data"]["code"]) == "0":
                        self.update_status.emit("登录成功")
                        headers = getter.get_headers()
                        login_status = True
                    elif str(status["data"]["code"]) == "86101":
                        self.update_status.emit("请扫描二维码登录bilibili")
                    elif str(status["data"]["code"]) == "86090":
                        self.update_status.emit("扫描成功，请确认")
                    elif str(status["data"]["code"]) == "86038":
                        err_msg = "二维码失效"
                        break
                    else:
                        err_msg = "二维码登录错误"
                        break
                    time.sleep(1.2)
            if self.parent().dialog_end:
                self.self_finished()
                return
            if not login_status:
                self.update_status.emit(err_msg)
                time.sleep(1)
                self.self_finished()
                return
            # cookie = cookieTools.get_cookie(status["data"]["url"])
            cookie = cookieTools.get_cookie_v2(headers.get_all("Set-Cookie"))
            ts = cookieTools.format_date_to_timestamp(cookie["Expires"])
            key = passport.gen_key()
            cookie = passport.encode_cookie(cookie, key)
            ret = {"ts": ts, "secure_data": cookie}
            ret = pickle.dumps(ret)
            ret = QtCore.QByteArray(ret)
            self.update_data.emit(ret, key)
            time.sleep(1)
            self.self_finished()
        except Exception as e:
            err_msg = str(e)
            self.update_status.emit(err_msg)
            time.sleep(1)
            self.self_finished()
