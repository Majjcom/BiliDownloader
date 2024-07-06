import time
from copy import deepcopy
from hashlib import md5
from urllib.parse import urlsplit, urlencode

from . import get_api
from . import network
from .passport import BiliPassport
from ..exceptions import GetWbiException

__wbi_sign_data = None

_API = get_api(("user", "nav"))

_HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://www.bilibili.com/'
}


def _get_online_sign_data(passport: BiliPassport):
    headers = deepcopy(_HEADERS)
    if passport is not None:
        headers["cookie"] = passport.get_cookie()
    url = urlsplit(_API["url"])

    get: dict = network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=_API["method"],
        path=url.path,
        header=headers
    )

    if get["code"] != 0:
        if passport is not None:
            raise GetWbiException(
                "获取Wbi信息错误:\n{0}\n{1}\n{2}".format(
                    get["code"],
                    get["message"],
                    _API["return"]["code"].get(str(get["code"]), "未知错误")
                )
            )

    return get["data"]["wbi_img"]


def _gen_mixin_key(raw_key: str):
    _MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52
    ]
    ret = ""
    for i in _MIXIN_KEY_ENC_TAB:
        ret += raw_key[i]
    return ret[:32]


def _get_wbi_sign(passport: BiliPassport):
    global __wbi_sign_data
    if __wbi_sign_data is not None:
        return __wbi_sign_data

    wbi_data = _get_online_sign_data(passport)

    img_key = wbi_data["img_url"].rsplit("/", 1)[1].split(".", 1)[0]
    sub_key = wbi_data["sub_url"].rsplit("/", 1)[1].split(".", 1)[0]

    __wbi_sign_data = (img_key, sub_key)
    return __wbi_sign_data


def sign_params(params: dict, passport: BiliPassport):
    keys = _get_wbi_sign(passport)
    keys = keys[0] + keys[1]
    mixin_key = _gen_mixin_key(keys)
    curr_time = round(time.time())
    params['wts'] = curr_time
    params = dict(sorted(params.items()))
    params = {
        k: ''.join(filter(lambda ch: ch not in "!'()*", str(v)))
        for k, v
        in params.items()
    }
    query = urlencode(params)
    wbi_sign = md5((query + mixin_key).encode("utf_8")).hexdigest()
    params['w_rid'] = wbi_sign
    return params
