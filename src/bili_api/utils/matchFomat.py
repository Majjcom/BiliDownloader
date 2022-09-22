from typing import Union, List
import re

_fmatchers = [re.compile(r'(BV|bv)(?=[\d,a-zA-Z]{10})'), re.compile(r'(AV|av)(?=\d+)'), re.compile(r'(EP|ep)(?=\d+)'),
              re.compile(r'(MD|md)(?=\d+)')]

_matchers = [re.compile(r'(BV|bv)[\d,a-zA-z]{10}'), re.compile(r'(AV|av)\d+'), re.compile(r'(EP|ep)\d+'),
             re.compile(r'(MD|md)\d+')]


def matchAll(in_: str) -> Union[str, None]:
    matches: List[re.Match] = []
    for i in _fmatchers:
        matches.append(i.search(in_))
    noneCount = 0
    for i in matches:
        if i is None:
            noneCount += 1
    if noneCount >= len(matches):
        return None
    if noneCount < len(_fmatchers) - 1:
        return None
    for i in matches:
        if i is not None:
            return i.group().upper()


def getBvid(in_: str) -> Union[str, None]:
    matcher = _matchers[0]
    get = matcher.search(in_)
    if get is None:
        return None
    return get.group()


def getAvid(in_: str) -> Union[str, None]:
    matcher = _matchers[1]
    get = matcher.search(in_)
    if get is None:
        return None
    return get.group()


def getEpid(in_: str) -> Union[str, None]:
    matcher = _matchers[2]
    get = matcher.search(in_)
    if get is None:
        return None
    return get.group()


def getMdid(in_: str) -> Union[str, None]:
    matcher = _matchers[3]
    get = matcher.search(in_)
    if get is None:
        return None
    return get.group()


if __name__ == '__main__':
    print(matchAll('https://www.bilibili.com/video/ep2434243?spm_id_from=333.851.b_7265636f6d6d656e64.1'))
