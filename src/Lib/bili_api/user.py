import copy
from urllib.parse import urlsplit

from . import utils

API = utils.get_api(("user",))


def get_login_url():
    api = copy.deepcopy(API["get_login_url"])
    url = urlsplit(api["url"])
    get = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api["method"],
        path=url.path,
    )
    return {"data": get["data"]}


class Get_login_info(utils.network.DataGetter):
    def __init__(self, key: str):
        api = copy.deepcopy(API["get_login_data"])
        url = urlsplit(api["url"])
        params = api["params"]
        params["qrcode_key"] = key
        super().__init__(
            scheme=url.scheme,
            host=url.netloc,
            method=api["method"],
            path=url.path,
            query=params,
        )
        self.link()


def get_login_url_old():
    api = copy.deepcopy(API["get_login_url_old"])
    url = urlsplit(api["url"])
    get = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api["method"],
        path=url.path,
    )
    return {"data": get["data"]}


class Get_login_info_old(utils.network.DataGetter):
    def __init__(self, oauthKey: str):
        api = copy.deepcopy(API["get_login_data_old"])
        url = urlsplit(api["url"])
        params = api["params"]
        params.pop("gourl")
        params["oauthKey"] = oauthKey
        super().__init__(
            scheme=url.scheme,
            host=url.netloc,
            method=api["method"],
            path=url.path,
            query=params,
        )
        self.link()


def exit_login(passport: utils.BiliPassport):
    api = copy.deepcopy(API["exit"])
    url = urlsplit(api["url"])
    params = api["params"]
    params.pop("gourl")
    params["biliCSRF"] = passport.get_data()["bili_jct"]
    get = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api["method"],
        path=url.path,
        query=params,
        header={"cookie": passport.get_cookie()}
    )

    if get["code"] != 0:
        raise utils.network.NetWorkException("退出登录失败:\n{0};\n{1};\n2{2};".format(
            get["code"],
            api["return"]["code"].get(str(get["code"]), "未知错误"),
            get.get("message", "未知错误")
        ))

    return True
