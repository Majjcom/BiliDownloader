import hashlib
import time
import traceback
from urllib.request import Request, urlopen

from PySide2 import QtCore

from Lib.bd_client import BDClient
from utils import version

HOST = "www.majjcom.site"


class UpdateChecker(QtCore.QThread):
    def __init__(self, parent: QtCore.QObject | None = ...) -> None:
        super().__init__(parent)
        self.timer_finished = False

    def run(self) -> None:
        c = BDClient(HOST, 11289)
        get = c.request({
            "act": "ver",
            "ver": version.__version__
        })
        c.close()
        new_ver = get["ver"]
        if not version.check_update(new_ver):
            return
        del c
        c = BDClient(HOST, 11289)
        get = c.request({
            "act": "info",
            "ver": version.__version__
        })
        c.close()
        info = get["data"]
        self.emit(QtCore.SIGNAL("find_update(QString, QString)"), new_ver, info)


class UpdateDownloader(QtCore.QThread):
    def __init__(self, parent: QtCore.QObject | None = ...) -> None:
        super().__init__(parent)

    def setup(self, path: str):
        self.timer_finished = False
        # self.file_name = "BiliDownloader_Installer.exe"
        self.dir_path = path
        # self.save_path = QtCore.QDir(path).absoluteFilePath(self.file_name)

    # Slot
    def timer_timeout(self):
        self.emit(QtCore.SIGNAL("update_process(int, int)"), self.size, self.total)
        if self.size == self.total:
            self.timer.stop()
            self.timer_finished = True

    def run(self):
        try:
            s = BDClient(HOST, 11289)
            get = s.request({
                "act": "url",
                "ver": version.__version__
            })
            s.close()
            self.url = get["url"]
            self.file_hash = get["hash"]
            self.file_name = get["name"]
            self.save_path = QtCore.QDir(self.dir_path).absoluteFilePath(self.file_name)

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
