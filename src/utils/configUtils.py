import json
import os
import copy
import threading

from . import version


_memory_data = None
_memory_lock = threading.RLock()


def enable_memory_mode():
    """Load the existing configuration once; subsequent changes stay in memory."""
    global _memory_data
    with _memory_lock:
        if os.path.isfile("data/userdata.json"):
            with open("data/userdata.json", "r", encoding="utf_8") as f:
                _memory_data = json.load(f)
        else:
            _memory_data = {
                "version": version.__version__,
                "isnew": False,
                "userinfo": {},
            }


def _read_data():
    with _memory_lock:
        if _memory_data is not None:
            return copy.deepcopy(_memory_data)
    setupUserData()
    with open("data/userdata.json", "r", encoding="utf_8") as f:
        return json.load(f)


def _write_data(data):
    global _memory_data
    with _memory_lock:
        if _memory_data is not None:
            # Login state is immutable for the entire headless session.
            data = copy.deepcopy(data)
            for key in (Configs.PASSPORT, Configs.PASSPORT_CRYPT_KEY):
                if key in _memory_data["userinfo"]:
                    data["userinfo"][key] = copy.deepcopy(_memory_data["userinfo"][key])
                else:
                    data["userinfo"].pop(key, None)
            _memory_data = data
            return
    with open("data/userdata.json", "w", encoding="utf_8") as f:
        json.dump(data, f, sort_keys=True, indent=2)


class Configs:
    VIDEO_CODEC = "video_codec"
    DOWNLOAD_PATH = "downloadPath"
    RESERVE_AUDIO = "reserveAudio"
    SAVE_DANMAKU = "saveDanmaku"
    MAX_THREAD_COUNT = "max_thread_count"
    PASSPORT = "passport"
    ULTRA_RESOLUTION = "ultra_resolution"
    SHOW_DOWNLOAD_TIP = "show_download_tip"
    QT_STYLE = "qt_ui_style"
    DOWNLOAD_AUDIO_ONLY = "download_audio_only"
    APPLY_HIGH_DPI = "apply_high_dpi"
    PASSPORT_CRYPT_KEY = "passport_crypt_key"
    DISABLE_TITLE_LENGTH_LIMIT = "disable_title_length_limit"
    AUTO_FILL_DATA_FROM_CLIPBOARD = "auto_fill_data_from_clipboard"
    PULL_DOLBY_AUDIO = "pull_dolby_audio"


def setupUserData(reset: bool = False) -> None:
    if _memory_data is not None:
        return
    if not os.path.exists("data"):
        os.mkdir("data")
    if not os.path.exists("data/userdata.json"):
        with open("data/userdata.json", "w", encoding="utf_8") as f:
            meta = {
                "version": version.__version__,
                "isnew": False if reset else True,
                "userinfo": dict(),
            }
            json.dump(meta, f, sort_keys=True, indent=2)


class UserDataHelper:
    def __init__(self, autosave=False):
        self.CFGS: Configs = Configs()
        self.raw = _read_data()
        self.KEYWD = ("version", "isnew")
        self.autosave = autosave
        self.changed = False

    def set(self, key: str, value: {dict, list, int, float, str, None}):
        if _memory_data is not None and key in (Configs.PASSPORT, Configs.PASSPORT_CRYPT_KEY):
            raise ValueError("headless 模式不允许修改登录信息")
        if key in self.KEYWD:
            self.raw[key] = value
            self.changed = True
            return

        # Erase value
        if value is None:
            self.raw["userinfo"].pop(key, None)
            self.changed = True
            return

        # Save same value
        if self.raw["userinfo"].get(key, None) == value:
            return

        # Set value
        self.raw["userinfo"][key] = value
        self.changed = True

        if self.autosave:
            self.save()

    def get(self, key, default=None):
        if key in self.KEYWD:
            return self.raw.get(key, default)
        return self.raw["userinfo"].get(key, default)

    def save(self):
        if not self.changed:
            return
        _write_data(self.raw)
        self.changed = False

    def reload(self):
        self.raw = _read_data()
        self.changed = False


def getUserData(key: str, default=None):
    keywd = ("version", "isnew")
    userdata = _read_data()
    if key in keywd:
        return userdata[key]
    if key in userdata["userinfo"]:
        return userdata["userinfo"][key]
    return default


def setUserData(key: str, value: {dict, list, int, float, str, None}) -> bool:
    if _memory_data is not None and key in (Configs.PASSPORT, Configs.PASSPORT_CRYPT_KEY):
        raise ValueError("headless 模式不允许修改登录信息")
    keywd = ("version", "isnew")
    userdata = _read_data()
    if key in keywd:
        userdata[key] = value
    else:
        if value is None:
            userdata["userinfo"].pop(key, None)
        else:
            userdata["userinfo"][key] = value
    _write_data(userdata)
    return True


def reSetUserData():
    if _memory_data is not None:
        _write_data({
            "version": version.__version__,
            "isnew": False,
            "userinfo": {},
        })
        return
    setupUserData()
    os.remove("data/userdata.json")
    setupUserData(reset=True)
