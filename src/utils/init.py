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
        configUtils.setUserData("isnew", False)
        configUtils.setUserData("version", version.__version__)
        return True
    return False
