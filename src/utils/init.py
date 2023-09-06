from . import configUtils
from . import version
import os


def init():
    if not os.path.exists("Download"):
        os.mkdir("Download")
    configUtils.setupUserData(True)
    status = configUtils.getUserData("isnew")
    status = (
        version.check_version(
            version.__version__, configUtils.getUserData("version", version.__version__)
        )
        or status
    )
    if status:
        if os.path.exists("CHANGELOG.txt"):
            os.startfile("CHANGELOG.txt")
        configUtils.setUserData("isnew", False)
