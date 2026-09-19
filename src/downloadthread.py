import copy
import http.client
import os
import re
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PySide6 import QtCore

from Lib.bili_api import video, danmaku, bangumi
from Lib.bili_api.utils import BiliPassport
from Lib.bili_api.utils.passport import decode_cookie
from Lib.xml2ass import convertMain
from utils import configUtils

_DEFAULT_HEADERS = {
    "Referer": "https://www.bilibili.com",
    "User-Agent": "Mozilla/5.0",
    "Accept-Encoding": "identity",
}
_NETWORK_TIMEOUT = 15

RESULT_COMPLETED = "completed"
RESULT_PAUSED = "paused"
RESULT_FAILED = "failed"
RESULT_CANCELLED = "cancelled"


class DownloadPaused(Exception):
    pass


class DownloadCancelled(Exception):
    pass


class StreamChanged(Exception):
    pass


class MediaSourceUnavailable(Exception):
    def __init__(self, message, refresh_immediately=False):
        super().__init__(message)
        self.refresh_immediately = refresh_immediately


def download_danmaku(path, cid):
    danmakuXml = danmaku.get_danmaku_xml(cid)
    danmakuAss = convertMain(danmakuXml, 852, 480, text_opacity=0.6)
    with open(path, "w", encoding="utf_8") as f:
        f.write(danmakuAss)


class DownloadTask(QtCore.QThread):
    update_progress = QtCore.Signal("quint64", "quint64")
    update_status = QtCore.Signal(str)
    enable_restart = QtCore.Signal()
    update_finished = QtCore.Signal()
    pause_available = QtCore.Signal(bool)
    actions_available = QtCore.Signal(bool)

    def __init__(self, parent: QtCore.QObject = ...) -> None:
        super().__init__(parent)
        self.video_finished_size = 0
        self.audio_finished_size = 0
        self.total_size = 0
        self.task = None
        self.result = RESULT_FAILED
        self._pause_requested = threading.Event()
        self._cancel_requested = threading.Event()
        self._protected_stage = threading.Event()
        self._control_lock = threading.Lock()
        self._last_progress_update = 0.0
        self._using_cached_media = False
        self._media_refresh_attempted = False
        self._process = None
        self._process_lock = threading.Lock()

    def setup(self, task: dict):
        self.task = task
        self.task.setdefault("streamStates", {})

    def request_pause(self):
        with self._control_lock:
            if self._protected_stage.is_set():
                return False
            self._pause_requested.set()
            return True

    def request_cancel(self):
        with self._control_lock:
            if self._protected_stage.is_set():
                return False
            self._cancel_requested.set()
        with self._process_lock:
            process = self._process
        if process is not None and process.poll() is None:
            process.terminate()
        return True

    def t_stop(self):
        self.request_cancel()

    def is_interruptible(self):
        with self._control_lock:
            return not self._protected_stage.is_set()

    def _protect_remaining_stages(self):
        with self._control_lock:
            self._check_control()
            self._protected_stage.set()
        self.actions_available.emit(False)

    def _check_control(self):
        if self._cancel_requested.is_set():
            raise DownloadCancelled()
        if self._pause_requested.is_set():
            raise DownloadPaused()

    def _retry_delay(self):
        end_time = time.monotonic() + 2
        while time.monotonic() < end_time:
            self._check_control()
            time.sleep(0.1)

    def _retry_media_source(self, error, description, try_times):
        max_attempts = 2 if self._using_cached_media else 3
        if error.refresh_immediately or try_times + 1 >= max_attempts:
            raise error
        self.update_status.emit(
            "{}失败，即将重试，次数{}".format(description, try_times + 1)
        )
        self._retry_delay()

    @staticmethod
    def _network_error(error):
        return isinstance(
            error,
            (
                URLError,
                TimeoutError,
                ConnectionError,
                http.client.HTTPException,
                OSError,
            ),
        )

    @staticmethod
    def _http_source_error(error):
        immediate = error.code in (401, 403, 404, 410, 416)
        return MediaSourceUnavailable(
            "下载链接返回状态码 {}".format(error.code), immediate
        )

    def _emit_progress(self, force=False):
        now = time.monotonic()
        if force or now - self._last_progress_update >= 0.1:
            self.update_progress.emit(
                self.video_finished_size + self.audio_finished_size,
                self.total_size,
            )
            self._last_progress_update = now

    def _set_stream_progress(self, stream_kind, size):
        if stream_kind == "video":
            self.video_finished_size = size
        else:
            self.audio_finished_size = size
        self._emit_progress()

    @staticmethod
    def _content_range(response):
        value = response.headers.get("Content-Range", "")
        match = re.match(r"bytes (\d+)-(\d+)/(\d+|\*)", value)
        if match is None:
            return None
        total = None if match.group(3) == "*" else int(match.group(3))
        return int(match.group(1)), int(match.group(2)), total

    @staticmethod
    def _response_validator(response):
        etag = response.headers.get("ETag")
        if etag and not etag.startswith("W/"):
            return {"type": "etag", "value": etag}
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            return {"type": "last-modified", "value": last_modified}
        return None

    def _prepare_stream_identity(
            self, stream_kind, url, path, expected_size, validator
    ):
        old_state = self.task["streamStates"].get(stream_kind)
        old_path = old_state.get("path") if old_state is not None else None
        if old_path and old_path != path and os.path.exists(old_path):
            os.remove(old_path)

        local_size = os.path.getsize(path) if os.path.exists(path) else 0
        same_resource = False
        if old_state is not None and old_state.get("size") == expected_size:
            old_validator = old_state.get("validator")
            if validator is not None and old_validator is not None:
                same_resource = old_validator == validator
            elif old_state.get("url") == url:
                same_resource = True

        if local_size and not same_resource:
            with open(path, "wb"):
                pass
            self._set_stream_progress(stream_kind, 0)

        self.task["streamStates"][stream_kind] = {
            "url": url,
            "path": path,
            "size": expected_size,
            "validator": validator,
            "complete": same_resource and local_size == expected_size,
        }

    def _discard_stream_state(self, stream_kind):
        state = self.task["streamStates"].get(stream_kind)
        if state is None:
            return
        path = state.get("path")
        if path and os.path.exists(path):
            os.remove(path)
        self.task["streamStates"].pop(stream_kind, None)

    def _probe_stream_size(self, url, description, stream_kind, path):
        for try_times in range(3):
            try:
                self._check_control()
                self.update_status.emit("正在获取{}流信息".format(description))
                headers = dict(_DEFAULT_HEADERS)
                headers["Range"] = "bytes=0-0"
                req = Request(url=url, method="GET", headers=headers)
                with urlopen(req, timeout=_NETWORK_TIMEOUT) as resp:
                    status = getattr(resp, "status", resp.getcode())
                    content_range = self._content_range(resp)
                    validator = self._response_validator(resp)
                    if status == 206:
                        if content_range is None or content_range[2] is None:
                            raise MediaSourceUnavailable(
                                "服务器返回了无效的文件范围", True
                            )
                        expected_size = content_range[2]
                    else:
                        content_length = resp.headers.get("Content-Length")
                        if status != 200 or content_length is None:
                            raise MediaSourceUnavailable(
                                "服务器未返回文件大小", True
                            )
                        expected_size = int(content_length)
            except (DownloadPaused, DownloadCancelled):
                raise
            except HTTPError as error:
                try:
                    source_error = self._http_source_error(error)
                finally:
                    error.close()
                self._retry_media_source(
                    source_error, "获取{}流信息".format(description), try_times
                )
                continue
            except MediaSourceUnavailable as error:
                self._retry_media_source(
                    error, "获取{}流信息".format(description), try_times
                )
                continue
            except Exception as error:
                if not self._network_error(error):
                    raise
                self._retry_media_source(
                    MediaSourceUnavailable(str(error)),
                    "获取{}流信息".format(description),
                    try_times,
                )
                continue

            self._prepare_stream_identity(
                stream_kind, url, path, expected_size, validator
            )
            return expected_size
        raise MediaSourceUnavailable("获取{}流信息失败".format(description))

    def _download_stream(self, url, path, stream_kind, expected_size, description):
        if os.path.exists(path) and os.path.getsize(path) > expected_size:
            with open(path, "wb"):
                pass

        for try_times in range(3):
            try:
                self._check_control()
                offset = os.path.getsize(path) if os.path.exists(path) else 0
                if offset == expected_size:
                    self.task["streamStates"][stream_kind]["complete"] = True
                    self._set_stream_progress(stream_kind, offset)
                    self._emit_progress(force=True)
                    return

                headers = dict(_DEFAULT_HEADERS)
                if offset:
                    headers["Range"] = "bytes={}-".format(offset)
                    validator = self.task["streamStates"][stream_kind].get(
                        "validator"
                    )
                    if validator is not None:
                        headers["If-Range"] = validator["value"]
                req = Request(url=url, method="GET", headers=headers)
                self.update_status.emit("正在下载{}".format(description))

                try:
                    response = urlopen(req, timeout=_NETWORK_TIMEOUT)
                except HTTPError as error:
                    try:
                        raise self._http_source_error(error)
                    finally:
                        error.close()
                except Exception as error:
                    if self._network_error(error):
                        raise MediaSourceUnavailable(str(error))
                    raise

                with response as resp:
                    status = getattr(resp, "status", resp.getcode())
                    mode = "wb"
                    write_offset = 0
                    if status == 206:
                        content_range = self._content_range(resp)
                        if content_range is None or content_range[0] != offset:
                            raise MediaSourceUnavailable(
                                "服务器返回了无效的续传范围", True
                            )
                        if (
                                content_range[2] is not None
                                and content_range[2] != expected_size
                        ):
                            raise MediaSourceUnavailable(
                                "续传文件大小发生变化", True
                            )
                        expected_validator = self.task["streamStates"][
                            stream_kind
                        ].get("validator")
                        response_validator = self._response_validator(resp)
                        if (
                                offset
                                and expected_validator is not None
                                and response_validator is not None
                                and response_validator != expected_validator
                        ):
                            raise StreamChanged()
                        if not offset:
                            self.task["streamStates"][stream_kind][
                                "validator"
                            ] = response_validator
                        mode = "ab"
                        write_offset = offset
                    elif status == 200:
                        # If the server ignored Range, restart instead of appending data.
                        self.task["streamStates"][stream_kind][
                            "validator"
                        ] = self._response_validator(resp)
                        mode = "wb"
                    elif status not in (200, 206):
                        raise MediaSourceUnavailable(
                            "下载请求返回状态码 {}".format(status),
                            status in (401, 403, 404, 410, 416),
                        )

                    self._set_stream_progress(stream_kind, write_offset)
                    with open(path, mode) as f:
                        while True:
                            try:
                                buffer = resp.read(64 * 1024)
                            except Exception as error:
                                if self._network_error(error):
                                    raise MediaSourceUnavailable(str(error))
                                raise
                            if not buffer:
                                break
                            f.write(buffer)
                            write_offset += len(buffer)
                            self._set_stream_progress(stream_kind, write_offset)
                            self._check_control()

                actual_size = os.path.getsize(path)
                self._set_stream_progress(stream_kind, actual_size)
                if actual_size != expected_size:
                    raise MediaSourceUnavailable(
                        "{}流大小不完整：{} / {}".format(
                            description, actual_size, expected_size
                        )
                    )
                self._emit_progress(force=True)
                self.task["streamStates"][stream_kind]["complete"] = True
                return
            except (DownloadPaused, DownloadCancelled):
                raise
            except StreamChanged:
                with open(path, "wb"):
                    pass
                self.task["streamStates"][stream_kind]["complete"] = False
                self._set_stream_progress(stream_kind, 0)
            except MediaSourceUnavailable as error:
                self._retry_media_source(
                    error, "下载{}".format(description), try_times
                )
        raise MediaSourceUnavailable("下载{}失败".format(description))

    def download_dash(self, get_url: dict, root_dir: QtCore.QDir):
        video_urls: list = get_url["dash"]["video"]
        video_urls.sort(key=lambda x: x["id"], reverse=True)
        quality = self.task["quality"]
        codec = self.task["codec"]
        available_qualities = [item["id"] for item in video_urls]
        quality = max(
            (item for item in available_qualities if item <= quality),
            default=min(available_qualities),
        )
        qid_match = [item for item in video_urls if item["id"] == quality]
        qid_match.sort(key=lambda x: x["codecid"])
        video_url = qid_match[0]["baseUrl"]
        for item in qid_match:
            if item["codecid"] == codec:
                video_url = item["baseUrl"]

        audio_streams = get_url["dash"].get("audio") or []
        audio_streams.sort(key=lambda x: x["bandwidth"], reverse=True)
        get_url["dash"]["audio"] = audio_streams

        selected_flac = False
        if self.task["specialAudio"] is not None:
            special_audio = self.task["specialAudio"]
            aud_stream_data = None
            try:
                if special_audio == "flac":
                    aud_stream_data = get_url["dash"]["flac"]["audio"]
                elif special_audio == "dolby":
                    aud_stream_data = get_url["dash"]["dolby"]["audio"][0]
            except (KeyError, IndexError, TypeError):
                pass
            if aud_stream_data is not None:
                get_url["dash"]["audio"].insert(0, aud_stream_data)
                selected_flac = special_audio == "flac"

        audio_url = None
        try:
            audio_url = get_url["dash"]["audio"][0]["baseUrl"]
        except (KeyError, IndexError, TypeError):
            pass
        if audio_url is None:
            self._discard_stream_state("audio")
            if self.task["onlyAudio"]:
                raise RuntimeError("当前视频没有可下载的音频流")

        video_temp_file_name = "{}_temp.mp4".format(self.task["tempName"])
        video_temp_file_path = root_dir.absoluteFilePath(video_temp_file_name)
        audio_extension = "flac" if selected_flac else "m4a"
        audio_temp_file_name = "{}_temp.{}".format(
            self.task["tempName"], audio_extension
        )
        audio_temp_file_path = root_dir.absoluteFilePath(audio_temp_file_name)

        video_size = 0
        if not self.task["onlyAudio"]:
            video_size = self._probe_stream_size(
                video_url, "视频", "video", video_temp_file_path
            )
        audio_size = 0
        if audio_url is not None:
            audio_size = self._probe_stream_size(
                audio_url, "音频", "audio", audio_temp_file_path
            )

        self.total_size = video_size + audio_size
        self.video_finished_size = 0
        self.audio_finished_size = 0
        self.enable_restart.emit()
        self.pause_available.emit(True)

        if not self.task["onlyAudio"]:
            self._download_stream(
                video_url, video_temp_file_path, "video", video_size, "视频"
            )

        self._check_control()

        if audio_url is not None:
            self._download_stream(
                audio_url, audio_temp_file_path, "audio", audio_size, "音频"
            )

        self._check_control()
        self._protect_remaining_stages()
        self._check_control()

        do_merge = not self.task["onlyAudio"] and audio_url is not None
        if do_merge:
            self.dash_ffmpeg_merge_video(
                root_dir, video_temp_file_path, audio_temp_file_path
            )

        self.update_status.emit("正在清理")
        if audio_url is None and not self.task["onlyAudio"]:
            self._replace_file(
                root_dir, video_temp_file_name, "{}.mp4".format(self.task["name"])
            )
        elif not self.task["onlyAudio"]:
            if root_dir.exists(video_temp_file_name) and not root_dir.remove(
                    video_temp_file_name
            ):
                raise RuntimeError("无法清理视频临时文件")

        if audio_url is not None:
            if self.task["reserveAudio"] or self.task["onlyAudio"]:
                self._replace_file(
                    root_dir,
                    audio_temp_file_name,
                    "{}.{}".format(self.task["name"], audio_extension),
                )
            elif root_dir.exists(audio_temp_file_name) and not root_dir.remove(
                    audio_temp_file_name
            ):
                raise RuntimeError("无法清理音频临时文件")

    @staticmethod
    def _replace_file(root_dir, source_name, target_name):
        try:
            os.replace(
                root_dir.absoluteFilePath(source_name),
                root_dir.absoluteFilePath(target_name),
            )
        except OSError:
            raise RuntimeError("无法保存文件 {}".format(target_name))

    def dash_ffmpeg_merge_video(
            self, root_dir: QtCore.QDir, video_temp_file_path, audio_temp_file_path
    ):
        self.update_status.emit("正在使用ffmpeg合并")
        out_name = "{}.mp4".format(self.task["name"])
        merge_name = "{}_merge.mp4".format(self.task["tempName"])
        if root_dir.exists(merge_name) and not root_dir.remove(merge_name):
            raise RuntimeError("无法清理合并临时文件")
        ffmpeg_path = QtCore.QDir("ffmpeg").absoluteFilePath(
            "ffmpeg" + ("" if sys.platform == "linux" else ".upx.exe")
        )
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
            root_dir.absoluteFilePath(merge_name),
        ]
        with open(os.devnull, "w") as devnull:
            kwargs = {"stdout": devnull, "stderr": devnull}
            if sys.platform != "linux":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            process = subprocess.Popen(command, **kwargs)
            with self._process_lock:
                self._process = process
            if self._cancel_requested.is_set():
                process.terminate()
            try:
                result = process.wait()
            finally:
                with self._process_lock:
                    self._process = None
        self._check_control()
        if result != 0:
            raise RuntimeError("ffmpeg合并失败")
        self._replace_file(root_dir, merge_name, out_name)

    def download_mp4(self, get_url: dict, root_dir: QtCore.QDir):
        video_urls: list = get_url["durls"]
        video_urls.sort(key=lambda x: x["quality"], reverse=True)
        quality = self.task["quality"]
        available_qualities = [item["quality"] for item in video_urls]
        quality = max(
            (item for item in available_qualities if item <= quality),
            default=min(available_qualities),
        )
        qid_match = [item for item in video_urls if item["quality"] == quality]
        durls = qid_match[0]["durl"]
        if len(durls) != 1:
            raise RuntimeError("暂不支持多分段MP4下载")
        if self.task["onlyAudio"]:
            raise RuntimeError("MP4格式暂不支持仅下载音频")
        self._discard_stream_state("audio")
        video_url = durls[0]["url"]

        video_temp_file_name = "{}_temp.mp4".format(self.task["tempName"])
        video_temp_file_path = root_dir.absoluteFilePath(video_temp_file_name)
        video_size = self._probe_stream_size(
            video_url, "视频", "video", video_temp_file_path
        )
        self.total_size = video_size
        self.video_finished_size = 0
        self.audio_finished_size = 0
        self.enable_restart.emit()
        self.pause_available.emit(True)

        self._download_stream(
            video_url, video_temp_file_path, "video", video_size, "视频"
        )
        self._check_control()
        self._protect_remaining_stages()
        self._check_control()
        self._replace_file(
            root_dir, video_temp_file_name, "{}.mp4".format(self.task["name"])
        )

    def download_danmaku(self, root_dir: QtCore.QDir):
        danmaku_file_name = "{}.ass".format(self.task["name"])
        danmaku_temp_file_name = "{}_temp.ass".format(self.task["tempName"])
        try:
            self.update_status.emit("正在下载弹幕")
            download_danmaku(
                root_dir.absoluteFilePath(danmaku_temp_file_name), self.task["cid"]
            )
            self._replace_file(root_dir, danmaku_temp_file_name, danmaku_file_name)
        except Exception:
            self.update_status.emit("弹幕下载失败，已跳过")
            if root_dir.exists(danmaku_temp_file_name):
                root_dir.remove(danmaku_temp_file_name)
            time.sleep(1)

    def _get_urls(self, passport):
        try_times = 0
        while try_times < 3:
            try:
                self._check_control()
                self.update_status.emit("正在获取链接")
                if self.task["type"] == "video":
                    kwargs = {"cid": self.task["cid"], "fnval": self.task["fnval"],
                              "cur_language": self.task["aiLanguage"], "passport": passport,
                              "bvid" if self.task["isbvid"] else "avid": self.task["id"]}
                    return video.get_video_url(**kwargs)

                kwargs = {"cid": self.task["cid"], "fnval": self.task["fnval"], "passport": passport,
                          "bvid" if self.task["isbvid"] else "avid": self.task["id"]}
                return bangumi.get_bangumi_url(**kwargs)["video_info"]
            except (DownloadPaused, DownloadCancelled):
                raise
            except Exception:
                try_times += 1
                self.update_status.emit(
                    "获取链接失败，即将重试，次数{}".format(try_times)
                )
                if try_times >= 3 and self.task["type"] == "video":
                    self.update_status.emit("失败次数过多，尝试更换获取链接方式")
                    self.task["type"] = "bangumi"
                    try_times = 0
                self._retry_delay()
        raise RuntimeError("获取下载链接失败")

    def _resolve_media(self, passport, use_cache=True):
        cached_media = self.task.get("resolvedMedia") if use_cache else None
        if cached_media is not None:
            self.task["type"] = cached_media["type"]
            return copy.deepcopy(cached_media["data"]), True

        get_url = self._get_urls(passport)
        self.task["resolvedMedia"] = {
            "type": self.task["type"],
            "data": copy.deepcopy(get_url),
        }
        return copy.deepcopy(get_url), False

    def _download_media(self, get_url, root_dir):
        if self.task["type"] == "video":
            self.download_dash(get_url, root_dir)
        elif get_url["type"] == "DASH":
            self.download_dash(get_url, root_dir)
        elif get_url["type"] == "MP4":
            self.download_mp4(get_url, root_dir)
        else:
            raise RuntimeError("不支持的下载格式")

    def _run_download(self):
        self.update_status.emit("开始下载")
        self.pause_available.emit(True)

        root_dir = QtCore.QDir(self.task["path"])
        if not root_dir.exists(self.task["title"]):
            root_dir.mkdir(self.task["title"])
        if not root_dir.cd(self.task["title"]):
            raise RuntimeError("无法进入下载目录")

        passportRaw = configUtils.getUserData(configUtils.Configs.PASSPORT)
        passport = None
        if passportRaw is not None:
            if "data" not in passportRaw:
                key = configUtils.getUserData(
                    configUtils.Configs.PASSPORT_CRYPT_KEY
                )
                passportRaw["data"] = decode_cookie(passportRaw["secure_data"], key)
            if passportRaw["data"] is not None:
                passport_data = dict(passportRaw["data"])
                passport_data.pop("Expires", None)
                passport = BiliPassport(passport_data)

        get_url, used_cache = self._resolve_media(passport)
        self._using_cached_media = used_cache
        self._check_control()

        try:
            self._download_media(get_url, root_dir)
        except MediaSourceUnavailable:
            if self._media_refresh_attempted:
                raise
            self._media_refresh_attempted = True
            if used_cache:
                self.update_status.emit("原链接失效，正在刷新")
            else:
                self.update_status.emit("链接不可用，正在刷新")
            self.task.pop("resolvedMedia", None)
            self._using_cached_media = False
            self._check_control()
            get_url, _ = self._resolve_media(passport, use_cache=False)
            self._download_media(get_url, root_dir)

        self._check_control()
        self._protect_remaining_stages()
        self._check_control()
        if self.task["saveDanmaku"]:
            self.download_danmaku(root_dir)
            self._check_control()

    def run(self):
        try:
            self._run_download()
        except DownloadPaused:
            self.result = RESULT_PAUSED
            self.update_status.emit("已暂停")
        except DownloadCancelled:
            self.result = RESULT_CANCELLED
        except Exception as error:
            self.result = RESULT_FAILED
            self.update_status.emit("下载失败：{}".format(error))
        else:
            self.result = RESULT_COMPLETED
            self.update_status.emit("下载完成")
            self.update_finished.emit()
        finally:
            self.pause_available.emit(False)
            self._emit_progress(force=True)
