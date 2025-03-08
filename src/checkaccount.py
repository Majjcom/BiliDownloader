from enum import Enum

from PySide6.QtCore import QThread, QObject, SIGNAL

from Lib.bili_api.utils import checkAccount
from Lib.bili_api.utils.passport import BiliPassport, decode_cookie
from utils.configUtils import UserDataHelper


class ACCOUNT_STATUS(Enum):
    NO_LOGIN = 0
    NORMAL = 1
    FAIL = 2


def check_account() -> ACCOUNT_STATUS:
    userdata = UserDataHelper()
    passport = userdata.get(userdata.CONFIGS.PASSPORT)
    if passport is None:
        return ACCOUNT_STATUS.NO_LOGIN
    if "data" not in passport:
        passport["data"] = decode_cookie(passport["secure_data"])
        if passport["data"] is None:
            return ACCOUNT_STATUS.FAIL
    if checkAccount.check(BiliPassport(passport["data"])):
        return ACCOUNT_STATUS.NORMAL
    return ACCOUNT_STATUS.FAIL


class CheckAccountThread(QThread):
    def __init__(self, parent: QObject | None = ...):
        super().__init__(parent)

    def run(self):
        ret = True

        res = check_account()
        if res == ACCOUNT_STATUS.FAIL:
            ret = False

        self.emit(
            SIGNAL("check_account_finished(bool)"),
            ret
        )
