from .passport import BiliPassport
from .wbisign import _get_online_sign_data


def check(passport: BiliPassport):
    try:
        _get_online_sign_data(passport)
    except Exception as _:
        return False
    return True
