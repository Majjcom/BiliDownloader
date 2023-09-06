from . import version
import json
import os


def setupUserData(reset: bool = False) -> None:
    if not os.path.exists("data"):
        os.mkdir("data")
    if not os.path.exists("data/userdata.json"):
        with open("data/userdata.json", "w") as f:
            meta = {
                "version": version.__version__,
                "isnew": False if reset else True,
                "userinfo": dict(),
            }
            json.dump(meta, f, sort_keys=True, indent=2)


def getUserData(key: str, default=None):
    keywd = ("version", "isnew")
    setupUserData()
    with open("data/userdata.json", "r") as f:
        userdata = json.load(f)
    if key in keywd:
        return userdata[key]
    if key in userdata["userinfo"]:
        return userdata["userinfo"][key]
    return default


def setUserData(key: str, value: {dict, list, int, float, str, None}) -> bool:
    keywd = ("version", "isnew")
    setupUserData()
    with open("data/userdata.json", "r") as f:
        userdata: dict = json.load(f)
    if key in keywd:
        userdata[key] = value
    else:
        if value is None:
            userdata["userinfo"].pop(key)
        else:
            userdata["userinfo"][key] = value
    with open("data/userdata.json", "w") as f:
        json.dump(userdata, f, sort_keys=True, indent=2)
    return True


def reSetUserData():
    setupUserData()
    os.remove("data/userdata.json")
    setupUserData(reset=True)
