from . import configUtils
import os


def init():
    if not os.path.exists("Download"):
        os.mkdir("Download")
    configUtils.setupUserData(True)
    status = configUtils.getUserData("isnew")
    if status:
        if os.path.exists("CHANGELOG.txt"):
            os.startfile("CHANGELOG.txt")
        configUtils.setUserData("isnew", False)
