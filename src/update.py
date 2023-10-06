import hashlib
import time
import traceback
from urllib.request import Request, urlopen

from PySide2 import QtCore

from Lib.bdnet import client
from utils import version


class UpdateChecker(QtCore.QThread):
    def __init__(self, parent: QtCore.QObject | None = ...) -> None:
        super().__init__(parent)
        self.timer_finished = False

    def run(self) -> None:
        c = client.Connection("www.majjcom.site", 11288)
        c.sendMsg({"action": "version", "after": True, "bVersion": version.__version__})
        get = c.recvMsg()
        c.close()
        new_ver = get["content"]
        if not version.check_update(new_ver):
            return
        del c
        c = client.Connection("www.majjcom.site", 11288)
        c.sendMsg({"action": "updateInfo", "bVersion": version.__version__})
        get = c.recvMsg()
        c.close()
        info = get["content"]
        self.emit(QtCore.SIGNAL("find_update(QString, QString)"), new_ver, info)


class UpdateDownloader(QtCore.QThread):
    def __init__(self, parent: QtCore.QObject | None = ...) -> None:
        super().__init__(parent)

    def setup(self, path: str):
        self.timer_finished = False
        self.file_name = "BiliDownloader_Installer.exe"
        self.save_path = QtCore.QDir(path).absoluteFilePath(self.file_name)

    # Slot
    def timer_timeout(self):
        self.emit(QtCore.SIGNAL("update_process(int, int)"), self.size, self.total)
        if self.size == self.total:
            self.timer.stop()
            self.timer_finished = True

    def run(self):
        try:
            s = client.Connection("www.majjcom.site", 11288)
            s.sendMsg({"action": "updateUrl", "bVersion": version.__version__})
            get = s.recvMsg()
            s.close()
            self.url = get["content"]["url"]
            self.file_hash = get["content"]["hash"]

            self.size = 0
            self.total = 0

            builder = hashlib.md5()
            req = Request(url=self.url, method="GET")

            with urlopen(req) as resp:
                self.total = int(resp.headers["content-length"])
                self.timer = QtCore.QTimer()
                self.timer.setInterval(100)
                self.timer.timeout.connect(self.timer_timeout)
                self.timer.start()
                self.timer.moveToThread(self.thread())
                with open(self.save_path, "wb") as f:
                    while True:
                        buffer = resp.read(4096)
                        if not buffer:
                            break
                        f.write(buffer)
                        builder.update(buffer)
                        self.size += len(buffer)

            while not self.timer_finished:
                time.sleep(0.1)

            md5 = builder.hexdigest()

            if md5.lower() != self.file_hash.lower():
                raise Exception("下载哈希无法对应，下载错误")
            self.emit(QtCore.SIGNAL("downlaod_install(QString)"), self.save_path)
        except Exception as e:
            self.emit(
                QtCore.SIGNAL("download_err(QString)"),
                str(e) + "\n" + traceback.format_exc(),
            )

        return
