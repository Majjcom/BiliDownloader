import os

from . import configUtils
from . import version


def init():
    if not os.path.exists("Download"):
        os.mkdir("Download")
    configUtils.setupUserData(False)
    status = configUtils.getUserData("isnew")
    status = (
        version.check_version(
            version.__version__, configUtils.getUserData("version", version.__version__)
        )
        or status
    )
    if status:
        userdata = configUtils.UserDataHelper()
        userdata.set("isnew", False)
        userdata.set("version", version.__version__)
        userdata.save()
        return True
    return False
