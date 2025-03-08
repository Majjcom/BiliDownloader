import re

_cookieMakers = [re.compile(r'DedeUserID=([^&]+)'), re.compile(r'DedeUserID__ckMd5=([^&]+)'),
                 re.compile(r'Expires=([^&]+)'), re.compile(r'SESSDATA=([^&]+)'),
                 re.compile(r'bili_jct=([^&]+)')]


def make_cookie(cookies: dict):
    ret = ''
    for i in cookies:
        ret += i + '=' + cookies[i] + ';'
    return ret[:-1]


def get_cookie(url: str):
    ret: dict = {}
    for i in _cookieMakers:
        tmp = i.search(url).group().split('=', 1)
        ret[tmp[0]] = tmp[1]
    return ret
