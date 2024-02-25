import json
import os

from . import version


class Configs:
    VIDEO_CODEC = "video_codec"
    DOWNLOAD_PATH = "downloadPath"
    RESERVE_AUDIO = "reserveAudio"
    SAVE_DANMAKU = "saveDanmaku"
    MAX_THREAD_COUNT = "max_thread_count"
    PASSPORT = "passport"


def setupUserData(reset: bool = False) -> None:
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
        setupUserData()
        fp = open("data/userdata.json", "r", encoding="utf_8")
        self.CONFIGS: Configs = Configs()
        self.raw = json.load(fp)
        self.KEYWD = ("version", "isnew")
        self.autosave = autosave
        self.changed = False
        fp.close()

    def set(self, key: str, value: {dict, list, int, float, str, None}):
        self.changed = True
        if key in self.KEYWD:
            self.raw[key] = value
            return
        if key is None:
            self.raw["userinfo"].pop(key)
            return
        self.raw["userinfo"][key] = value
        if self.autosave:
            self.save()

    def get(self, key, default=None):
        if key in self.KEYWD:
            return self.raw["key"]
        return self.raw["userinfo"].get(key, default)

    def save(self):
        if not self.changed:
            return
        fp = open("data/userdata.json", "w", encoding="utf_8")
        json.dump(self.raw, fp, sort_keys=True, indent=2)
        fp.close()


def getUserData(key: str, default=None):
    keywd = ("version", "isnew")
    setupUserData()
    with open("data/userdata.json", "r", encoding="utf_8") as f:
        userdata = json.load(f)
    if key in keywd:
        return userdata[key]
    if key in userdata["userinfo"]:
        return userdata["userinfo"][key]
    return default


def setUserData(key: str, value: {dict, list, int, float, str, None}) -> bool:
    keywd = ("version", "isnew")
    setupUserData()
    with open("data/userdata.json", "r", encoding="utf_8") as f:
        userdata: dict = json.load(f)
    if key in keywd:
        userdata[key] = value
    else:
        if value is None:
            userdata["userinfo"].pop(key)
        else:
            userdata["userinfo"][key] = value
    with open("data/userdata.json", "w", encoding="utf_8") as f:
        json.dump(userdata, f, sort_keys=True, indent=2)
    return True


def reSetUserData():
    setupUserData()
    os.remove("data/userdata.json")
    setupUserData(reset=True)
