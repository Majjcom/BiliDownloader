import re

def make_cookie(cookies: dict):
    ret = ''
    for i in cookies:
        ret += i + '=' + cookies[i] + ';'
    return ret[:-1]

def get_cookie(url: str):
    ret: dict = {}
    res = []
    res.append(re.compile(r'DedeUserID=.+(?=&DedeUserID__ckMd5=)'))
    res.append(re.compile(r'DedeUserID__ckMd5=.+(?=&Expires=)'))
    res.append(re.compile(r'Expires=.+(?=&SESSDATA=)'))
    res.append(re.compile(r'SESSDATA=.+(?=&bili_jct=)'))
    res.append(re.compile(r'bili_jct=.+(?=&gourl=)'))
    for i in res:
        tmp = i.search(url).group().split('=', 1)
        ret[tmp[0]] = tmp[1]
    return ret
