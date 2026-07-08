import os
import subprocess
import sys
import time
from urllib.request import Request, urlopen

from PySide2 import QtCore

from Lib.bili_api import video, danmaku, bangumi
from Lib.bili_api.utils import BiliPassport
from Lib.bili_api.utils.passport import decode_cookie
from Lib.xml2ass import convertMain
from utils import configUtils

_DEFAULT_HEADERS = {
    "Referer": "https://www.bilibili.com",
    "User-Agent": "Mozilla/5.0",
}


def download_danmaku(path, cid):
    danmakuXml = danmaku.get_danmaku_xml(cid)
    danmakuAss = convertMain(danmakuXml, 852, 480, text_opacity=0.6)
    with open(path, "w", encoding="utf_8") as f:
        f.write(danmakuAss)


class TimerThread(QtCore.QThread):
    def __init__(self, parent: QtCore.QObject = ...) -> None:
        super().__init__(parent)
        self.tstop = False

    def stop(self):
        self.tstop = True

    def run(self):
        while not self.tstop:
            time.sleep(0.1)
            self.emit(
                QtCore.SIGNAL("ttimeout()")
            )
        self.deleteLater()


class DownloadTask(QtCore.QThread):
    def __init__(self, parent: QtCore.QObject = ...) -> None:
        super().__init__(parent)
        self.fource_stop = False
        self.video_finished_size = 0
        self.audio_finished_size = 0
        self.total_size = 0
        self.task = None
        self.timer_stopped = False
        self.timer = None

    def setup(self, task: dict):
        self.task = task

    def t_stop(self):
        self.fource_stop = True

    def timer_timeout(self):
        self.emit(
            QtCore.SIGNAL("update_progress(quint64, quint64)"),
            self.video_finished_size + self.audio_finished_size,
            self.total_size,
        )
        if self.video_finished_size + self.audio_finished_size == self.total_size and self.total_size != 0:
            self.timer.stop()
            self.timer_stopped = True

    def download_dash(self, get_url: dict, root_dir: QtCore.QDir):
        video_urls: list = get_url["dash"]["video"]
        video_urls.sort(key=lambda x: x["id"], reverse=True)
        quality = self.task["quality"]
        codec = self.task["codec"]
        if quality > video_urls[0]["id"]:
            quality = video_urls[0]["id"]
        qid_match = []
        for i in video_urls:
            if i["id"] == quality:
                qid_match.append(i)
        qid_match.sort(key=lambda x: x["codecid"])
        video_url = qid_match[0]["baseUrl"]
        for i in qid_match:
            if i["codecid"] == codec:
                video_url = i["baseUrl"]

        if get_url["dash"].get("audio", None) is not None:
            get_url["dash"]["audio"].sort(key=lambda x: x["bandwidth"], reverse=True)

        # process special audio stream
        if self.task["specialAudio"] is not None:
            special_audio = self.task["specialAudio"]
            aud_stream_data = None
            try:
                if special_audio == "flac":
                    aud_stream_data = get_url["dash"]["flac"]["audio"]
                elif special_audio == "dolby":
                    aud_stream_data = get_url["dash"]["dolby"]["audio"][0]
            except:
                pass
            if aud_stream_data is not None:
                get_url["dash"]["audio"].insert(0, aud_stream_data)

        audio_url = None
        try:
            # 处理可能出现无音频流的情况
            audio_url = get_url["dash"]["audio"][0]["baseUrl"]
        except:
            pass

        # Get size
        try_times = 0
        video_size = 0
        while try_times < 3:
            try:
                self.emit(QtCore.SIGNAL("update_status(QString)"), "正在获取视频流信息")
                if self.task["onlyAudio"]:
                    video_size = 0
                else:
                    req = Request(url=video_url, method="GET", headers=_DEFAULT_HEADERS)
                    with urlopen(req) as resp:
                        video_size = int(resp.headers["content-length"])
                if audio_url is not None:
                    self.emit(QtCore.SIGNAL("update_status(QString)"), "正在获取音频流信息")
                    req = Request(url=audio_url, method="GET", headers=_DEFAULT_HEADERS)
                    with urlopen(req) as resp:
                        audio_size = int(resp.headers["content-length"])
                else:
                    audio_size = 0
                break
            except Exception as _e:
                try_times += 1
                self.emit(
                    QtCore.SIGNAL("update_status(QString)"),
                    "获取视频信息失败，即将重试，次数{}".format(try_times),
                )
                time.sleep(2)
        else:
            self.emit(QtCore.SIGNAL("update_status(QString)"), "下载失败，请重新输入")
            self.task["finished"] = True
            return
        self.total_size = video_size + audio_size
        self.video_finished_size = 0
        self.audio_finished_size = 0

        self.emit(QtCore.SIGNAL("enable_restart()"))

        # Download video
        video_temp_file_base = "{}_temp.mp4"
        video_temp_file_name = video_temp_file_base.format(self.task["name"])
        video_temp_file_path = root_dir.absoluteFilePath(video_temp_file_name)
        if not self.task["onlyAudio"]:
            self.download_dash_video(video_url, video_temp_file_path)

        # Download audio
        audio_temp_file_base = "{}_temp.m4a"
        audio_temp_file_name = audio_temp_file_base.format(self.task["name"])
        audio_temp_file_path = root_dir.absoluteFilePath(audio_temp_file_name)
        if audio_url is not None:
            self.download_dash_audio(audio_url, audio_temp_file_path)

        # End Download
        while not self.timer_stopped:
            time.sleep(0.1)

        do_merge = True

        if self.task["onlyAudio"]:
            do_merge = False

        if audio_url is None:
            do_merge = False

        if self.task["specialAudio"] == "flac":
            tmp = audio_temp_file_name
            audio_temp_file_name = "{}_temp.flac".format(self.task["name"])
            audio_temp_file_path = root_dir.absoluteFilePath(audio_temp_file_name)
            root_dir.rename(tmp, audio_temp_file_name)

        if do_merge:
            self.dash_ffmpeg_merge_video(root_dir, video_temp_file_path, audio_temp_file_path)

        # Cleanup
        self.emit(QtCore.SIGNAL("update_status(QString)"), "正在清理")
        if audio_url is None:
            root_dir.rename(video_temp_file_name, "{}.mp4".format(self.task["name"]))
        else:
            root_dir.remove(video_temp_file_name)
        if self.task["reserveAudio"] or self.task["onlyAudio"]:
            if self.task["specialAudio"] == "flac":
                root_dir.rename(audio_temp_file_name, "{}.flac".format(self.task["name"]))
            else:
                root_dir.rename(audio_temp_file_name, "{}.m4a".format(self.task["name"]))
        elif audio_url is None:
            pass
        else:
            root_dir.remove(audio_temp_file_name)

    def download_dash_video(self, video_url: str, video_temp_file_path: str):
        # Download video
        req = Request(url=video_url, method="GET", headers=_DEFAULT_HEADERS)
        try_times = 0
        while try_times < 3:
            try:
                self.emit(QtCore.SIGNAL("update_status(QString)"), "正在下载视频")
                with open(video_temp_file_path, "wb") as f:
                    with urlopen(req) as resp:
                        while True:
                            buffer = resp.read(4096)
                            if self.fource_stop:
                                return
                            if not buffer:
                                break
                            f.write(buffer)
                            self.video_finished_size += len(buffer)
                break
            except Exception as _e:
                try_times += 1
                self.emit(
                    QtCore.SIGNAL("update_status(QString)"),
                    "下载视频失败，即将重试，次数{}".format(try_times),
                )
                time.sleep(2)
        else:
            self.emit(QtCore.SIGNAL("update_status(QString)"), "下载失败，请重新输入")
            self.task["finished"] = True
            return

    def download_dash_audio(self, audio_url, audio_temp_file_path):
        req = Request(url=audio_url, method="GET", headers=_DEFAULT_HEADERS)
        try_times = 0
        while try_times < 3:
            try:
                self.emit(QtCore.SIGNAL("update_status(QString)"), "正在下载音频")
                with open(audio_temp_file_path, "wb") as f:
                    with urlopen(req) as resp:
                        while True:
                            buffer = resp.read(4096)
                            if self.fource_stop:
                                return
                            if not buffer:
                                break
                            f.write(buffer)
                            self.audio_finished_size += len(buffer)
                break
            except Exception as _e:
                try_times += 1
                self.emit(
                    QtCore.SIGNAL("update_status(QString)"),
                    "下载音频失败，即将重试，次数{}".format(try_times),
                )
                time.sleep(2)
        else:
            self.emit(QtCore.SIGNAL("update_status(QString)"), "下载失败，请重新输入")
            self.task["finished"] = True
            return

    def dash_ffmpeg_merge_video(self, root_dir: QtCore.QDir, video_temp_file_path, audio_temp_file_path):
        self.emit(QtCore.SIGNAL("update_status(QString)"), "正在使用ffmpeg合并")
        out_name = "{}.mp4".format(self.task["name"])
        if root_dir.exists(out_name):
            root_dir.remove(out_name)
        ffmpeg_path = QtCore.QDir("ffmpeg").absoluteFilePath("ffmpeg" + ("" if sys.platform == "linux" else ".upx.exe"))
        devnull = open(os.devnull, "w")
        command = [
            ffmpeg_path,
            "-i",
            video_temp_file_path,
            "-i",
            audio_temp_file_path,
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            root_dir.absoluteFilePath(out_name)
        ]

        # 使用新版本ffmpeg，不需要此功能
        '''
        # 启用实验性选项
        if audio_temp_file_path.endswith(".flac"):
            command.append('-strict')
            command.append('-2')
        command.append()
        '''

        if sys.platform == "linux":
            subprocess.call(
                command,
                stdout=devnull,
                stderr=devnull,
            )
        else:
            subprocess.call(
                command,
                stdout=devnull,
                stderr=devnull,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        devnull.close()

    def download_mp4(self, get_url: dict, root_dir: QtCore.QDir):
        video_urls: list = get_url["durls"]
        video_urls.sort(key=lambda x: x["quality"], reverse=True)
        quality = self.task["quality"]
        if quality > video_urls[0]["quality"]:
            quality = video_urls[0]["quality"]
        qid_match = []
        for i in video_urls:
            if i["quality"] == quality:
                qid_match.append(i)
        video_url = qid_match[0]["durl"][0]["url"]

        # Get size
        try_times = 0
        while try_times < 3:
            try:
                self.emit(QtCore.SIGNAL("update_status(QString)"), "正在获取视频流信息")
                req = Request(url=video_url, method="GET", headers=_DEFAULT_HEADERS)
                with urlopen(req) as resp:
                    video_size = int(resp.headers["content-length"])
                break
            except Exception as _e:
                try_times += 1
                self.emit(
                    QtCore.SIGNAL("update_status(QString)"),
                    "获取视频信息失败，即将重试，次数{}".format(try_times),
                )
                time.sleep(2)
        else:
            self.emit(QtCore.SIGNAL("update_status(QString)"), "下载失败，请重新输入")
            self.task["finished"] = True
            return
        self.total_size = video_size
        self.video_finished_size = 0
        self.audio_finished_size = 0

        self.emit(QtCore.SIGNAL("enable_restart()"))

        # Download video
        req = Request(url=video_url, method="GET", headers=_DEFAULT_HEADERS)
        video_temp_file_name = "{}_temp.mp4".format(self.task["name"])
        video_temp_file_path = root_dir.absoluteFilePath(video_temp_file_name)
        try_times = 0
        while try_times < 3:
            try:
                self.emit(QtCore.SIGNAL("update_status(QString)"), "正在下载视频")
                with open(video_temp_file_path, "wb") as f:
                    with urlopen(req) as resp:
                        while True:
                            buffer = resp.read(4096)
                            if self.fource_stop:
                                return
                            if not buffer:
                                break
                            f.write(buffer)
                            self.video_finished_size += len(buffer)
                break
            except Exception as _e:
                try_times += 1
                self.emit(
                    QtCore.SIGNAL("update_status(QString)"),
                    "下载视频失败，即将重试，次数{}".format(try_times),
                )
                time.sleep(2)
        else:
            self.emit(QtCore.SIGNAL("update_status(QString)"), "下载失败，请重新输入")
            self.task["finished"] = True
            return
        root_dir.rename(video_temp_file_name, "{}.mp4".format(self.task["name"]))

    def download_danmaku(self, root_dir: QtCore.QDir):
        danmaku_file_name = "{}.ass".format(self.task["name"])
        try:
            self.emit(QtCore.SIGNAL("update_status(QString)"), "正在下载弹幕")
            download_danmaku(
                root_dir.absoluteFilePath(danmaku_file_name), self.task["cid"]
            )
        except Exception as _:
            self.emit(QtCore.SIGNAL("update_status(QString)"), "弹幕下载失败，已跳过")
            if root_dir.exists(danmaku_file_name):
                root_dir.remove(danmaku_file_name)
            time.sleep(1)

    def run(self):
        self.emit(QtCore.SIGNAL("update_status(QString)"), "开始下载")

        # Creat directory
        root_dir = QtCore.QDir(self.task["path"])
        if not root_dir.exists(self.task["title"]):
            root_dir.mkdir(self.task["title"])
        root_dir.cd(self.task["title"])

        # Load Passport
        passportRaw = configUtils.getUserData(configUtils.Configs.PASSPORT)
        passport = None
        if passportRaw is not None:
            if "data" not in passportRaw:
                key = configUtils.getUserData(configUtils.Configs.PASSPORT_CRYPT_KEY)
                passportRaw["data"] = decode_cookie(passportRaw["secure_data"], key)
            if passportRaw["data"] is not None:
                passportRaw = passportRaw["data"]
                passportRaw.pop("Expires")
                passport = BiliPassport(passportRaw)

        # Get Urls
        try_times = 0
        while try_times < 3:
            try:
                self.emit(QtCore.SIGNAL("update_status(QString)"), "正在获取链接")
                get_url = None
                if self.task["type"] == "video":
                    ai_language = self.task["aiLanguage"]
                    if self.task["isbvid"]:
                        get_url = video.get_video_url(
                            bvid=self.task["id"],
                            cid=self.task["cid"],
                            fnval=self.task["fnval"],
                            cur_language=ai_language,
                            passport=passport
                        )
                    else:
                        get_url = video.get_video_url(
                            avid=self.task["id"],
                            cid=self.task["cid"],
                            fnval=self.task["fnval"],
                            cur_language=ai_language,
                            passport=passport
                        )
                elif self.task["type"] == "bangumi":
                    if self.task["isbvid"]:
                        get_url = bangumi.get_bangumi_url(
                            bvid=self.task["id"],
                            cid=self.task["cid"],
                            fnval=self.task["fnval"],
                            passport=passport,
                        )["video_info"]
                    else:
                        get_url = bangumi.get_bangumi_url(
                            avid=self.task["id"],
                            cid=self.task["cid"],
                            fnval=self.task["fnval"],
                            passport=passport,
                        )["video_info"]
                break
            except Exception as _e:
                try_times += 1
                self.emit(
                    QtCore.SIGNAL("update_status(QString)"),
                    "获取链接失败，即将重试，次数{}".format(try_times),
                )
                if try_times >= 3 and self.task["type"] == "video":
                    self.emit(
                        QtCore.SIGNAL("update_status(QString)"),
                        "失败次数过多，尝试更换获取链接方式"
                    )
                    time.sleep(1.0)
                    self.task["type"] = "bangumi"
                    try_times = 0
                time.sleep(2)
        else:
            self.emit(QtCore.SIGNAL("update_status(QString)"), "下载失败，请重新输入")
            self.task["finished"] = True
            return

        self.timer = TimerThread(None)
        self.connect(
            self.timer,
            QtCore.SIGNAL("ttimeout()"),
            self.timer_timeout
        )
        self.timer_stopped = False
        self.timer.start()

        # parse urls
        if self.task["type"] == "video":
            self.download_dash(get_url, root_dir)
        elif self.task["type"] == "bangumi":
            if get_url["type"] == "DASH":
                self.download_dash(get_url, root_dir)
            elif get_url["type"] == "MP4":
                self.download_mp4(get_url, root_dir)

        if self.fource_stop:
            return

        # Download and parse Xml Danmaku
        if self.task["saveDanmaku"]:
            self.download_danmaku(root_dir)

        time.sleep(0.2)

        self.emit(QtCore.SIGNAL("update_status(QString)"), "下载完成")
        self.emit(QtCore.SIGNAL("update_finished()"))
        self.task["finished"] = True
