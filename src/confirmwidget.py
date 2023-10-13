import pickle
import traceback
from urllib.request import urlopen

from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtCore import SIGNAL, Signal, QByteArray

from Lib.bili_api import video, bangumi
from Lib.bili_api.exceptions import NetWorkException
from ui_confirmwidget import Ui_ConfirmWidget


class ConfirmWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ConfirmWidget, self).__init__(parent)
        self.ui = Ui_ConfirmWidget()
        self.ui.setupUi(self)
        self.err = True

    def on_size_change(self):
        img = self.img.scaledToWidth(
            self.ui.cover_label.width(), QtCore.Qt.SmoothTransformation
        )
        self.ui.cover_label.setPixmap(QtGui.QPixmap.fromImage(img))

    def update_info(self, data: str, err: bool):
        self.ui.text_info.setText(data)
        self.err = err

    def update_image(self, img: QtGui.QImage):
        self.img = img
        self.on_size_change()

    def update_meta(self, data: QByteArray):
        self.meta = data

    def load_end(self):
        self.disconnect(self.load_thread)
        del self.load_thread
        if not self.err:
            self.ui.button_next.setEnabled(True)

    def data_update(self, back):
        self.img = QtGui.QImage(":/res/Placeholde.png")
        img = self.img.scaledToWidth(
            self.ui.cover_label.width(), QtCore.Qt.SmoothTransformation
        )
        self.ui.cover_label.setPixmap(QtGui.QPixmap.fromImage(img))
        self.ui.text_info.setText("")
        self.ui.button_next.setDisabled(True)
        format, content = self.parent().input_pages[0].get_content()
        self.load_thread = load_map[format](self, content)
        self.connect(
            self.load_thread,
            SIGNAL("update_info(QString, bool)"),
            self.update_info,
        )
        self.connect(
            self.load_thread,
            SIGNAL("update_image(QImage)"),
            self.update_image,
        )
        self.connect(
            self.load_thread,
            SIGNAL("update_meta(QByteArray)"),
            self.update_meta,
        )
        self.connect(self.load_thread, SIGNAL("finished()"), self.load_end)
        self.load_thread.start()


class LoadInfoBase(QtCore.QThread):
    def __init__(self, parent: ConfirmWidget, format: str, content: str) -> None:
        super(LoadInfoBase, self).__init__(parent)
        self.format = format
        self.content = content
        self.update_imgae = Signal(QtGui.QImage, name="update_imgae")
        self.update_info = Signal(str, bool, name="update_info")
        self.update_meta = Signal(QByteArray, name="update_meta")

    def run(self):
        try:
            self.load_data()
        except NetWorkException as ex:
            show = str(ex)
            self.emit(SIGNAL("update_info(QString, bool)"), show, True)
        except Exception as ex:
            show = "未知错误\n" + str(ex) + "\n\n"
            show += traceback.format_exc()
            self.emit(SIGNAL("update_info(QString, bool)"), show, True)

    def load_data(self):
        pass


class LaodInfoAV(LoadInfoBase):
    def __init__(self, parent: QtCore.QObject, aid: str) -> None:
        super(LaodInfoAV, self).__init__(parent, "AV", aid)

    def load_data(self):
        data = video.get_video_info(aid=self.content[2:])
        online = video.get_video_online_count(cid=data["cid"], aid=self.content[2:])
        pic_url = data["pic"]
        show: str = data["title"]
        show += "\n\nBV号: " + data["bvid"]
        show += "\nAV号: AV" + str(data["aid"])
        show += "\nUP主: " + data["owner"]["name"]
        show += "\n在线人数: " + online["total"]
        show += "\n\n简介:\n" + data["desc"]
        self.emit(SIGNAL("update_info(QString, bool)"), show, False)
        page_data = []
        for i in data["pages"]:
            part = {
                "isbvid": self.format == "BV",
                "id": self.content[2:],
                "cid": i["cid"],
                "page": i["page"],
                "name": i["part"],
                "title": data["title"],
            }
            page_data.append(part)
        meta_data = {}
        meta_data["title"] = data["title"]
        meta_data["page_data"] = page_data
        pack = pickle.dumps(meta_data)
        pack = QByteArray(pack)
        self.emit(SIGNAL("update_meta(QByteArray)"), pack)
        with urlopen(pic_url) as pic_data:
            img = QtGui.QImage.fromData(pic_data.read())
            self.emit(SIGNAL("update_image(QImage)"), img)


class LoadInfoBV(LoadInfoBase):
    def __init__(self, parent: QtCore.QObject, vid: str) -> None:
        super(LoadInfoBV, self).__init__(parent, "BV", vid)

    def load_data(self):
        data = video.get_video_info(bvid=self.content)
        online = video.get_video_online_count(cid=data["cid"], bvid=self.content)
        pic_url = data["pic"]
        show: str = data["title"]
        show += "\n\nBV号: " + data["bvid"]
        show += "\nAV号: AV" + str(data["aid"])
        show += "\nUP主: " + data["owner"]["name"]
        show += "\n在线人数: " + online["total"]
        show += "\n\n简介:\n" + data["desc"]
        self.emit(SIGNAL("update_info(QString, bool)"), show, False)
        page_data = []
        for i in data["pages"]:
            part = {
                "isbvid": self.format == "BV",
                "id": self.content,
                "cid": i["cid"],
                "page": i["page"],
                "name": i["part"],
                "title": data["title"],
            }
            page_data.append(part)
        meta_data = {}
        meta_data["title"] = data["title"]
        meta_data["page_data"] = page_data
        pack = pickle.dumps(meta_data)
        pack = QByteArray(pack)
        self.emit(SIGNAL("update_meta(QByteArray)"), pack)
        with urlopen(pic_url) as pic_data:
            img = QtGui.QImage.fromData(pic_data.read())
            self.emit(SIGNAL("update_image(QImage)"), img)


class LoadInfoMD(LoadInfoBase):
    def __init__(self, parent: QtCore.QObject, vid: str) -> None:
        super(LoadInfoMD, self).__init__(parent, "MD", vid)

    def load_data(self):
        data = bangumi.get_bangumi_info(self.content[2:])
        ssid = data["media"]["season_id"]
        ss_data = bangumi.get_bangumi_detailed_info(season_id=ssid)
        show = data["media"]["title"]
        show += "\n\nMD号: MD" + str(data["media"]["media_id"])
        show += "\n评分: " + str(data["media"]["rating"]["score"])
        show += "\n\n简介:\n" + ss_data["data"]["evaluate"]
        show += "\n\n制作:\n" + ss_data["data"]["staff"]
        cover_url = data["media"]["cover"]
        self.emit(SIGNAL("update_info(QString, bool)"), show, False)
        page_data = []
        i = 0
        for v in ss_data["data"]["episodes"]:
            part = {
                "isbvid": True,
                "id": v["bvid"],
                "cid": v["cid"],
                "page": i + 1,
                "name": v["title"] + "-" + v["long_title"],
                "title": data["media"]["title"],
            }
            page_data.append(part)
            i += 1
        meta_data = {}
        meta_data["title"] = data["media"]["season_id"]
        meta_data["page_data"] = page_data
        pack = pickle.dumps(meta_data)
        pack = QByteArray(pack)
        self.emit(SIGNAL("update_meta(QByteArray)"), pack)
        with urlopen(cover_url) as pic_data:
            img = QtGui.QImage.fromData(pic_data.read())
            self.emit(SIGNAL("update_image(QImage)"), img)


class LoadInfoEP(LoadInfoBase):
    def __init__(self, parent: ConfirmWidget, content: str) -> None:
        super().__init__(parent, "EP", content)

    def load_data(self):
        data = bangumi.get_bangumi_detailed_info(ep_id=self.content[2:])
        show = data["info"]["media"]["title"]
        show += "\n\nMD号: MD" + str(data["info"]["media"]["media_id"])
        show += "\n评分: " + str(data["info"]["media"]["rating"]["score"])
        show += "\n\n简介:\n" + data["data"]["evaluate"]
        show += "\n\n制作:\n" + data["data"]["staff"]
        cover_url = data["info"]["media"]["cover"]
        self.emit(SIGNAL("update_info(QString, bool)"), show, False)
        page_data = []
        i = 0
        for v in data["data"]["episodes"]:
            part = {
                "isbvid": True,
                "id": v["bvid"],
                "cid": v["cid"],
                "page": i + 1,
                "name": v["title"] + "-" + v["long_title"],
                "title": data["info"]["media"]["title"],
            }
            page_data.append(part)
            i += 1
        meta_data = {}
        meta_data["title"] = data["info"]["media"]["title"]
        meta_data["page_data"] = page_data
        pack = pickle.dumps(meta_data)
        pack = QByteArray(pack)
        self.emit(SIGNAL("update_meta(QByteArray)"), pack)
        with urlopen(cover_url) as pic_data:
            img = QtGui.QImage.fromData(pic_data.read())
            self.emit(SIGNAL("update_image(QImage)"), img)


load_map = {
    "AV": LaodInfoAV,
    "BV": LoadInfoBV,
    "MD": LoadInfoMD,
    "EP": LoadInfoEP,
}
