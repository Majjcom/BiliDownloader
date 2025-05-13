import socket

from .passport import BiliPassport
from .wbisign import _get_online_sign_data


def check(passport: BiliPassport):
    try:
        _get_online_sign_data(passport)
    except socket.error as _:
        return "NO_NETWORK"
    except Exception as _:
        return "FAIL"
    return "OK"
