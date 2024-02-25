import copy
from urllib.parse import urlsplit

from . import utils
from .exceptions.BiliVideoIdException import BiliVideoIdException
from .exceptions.NetWorkException import NetWorkException
from .utils import wbisign

API = utils.get_api(('video',))
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://www.bilibili.com/'
}


def __check_bvid(bvid: str) -> None:
    if len(bvid) != 12:
        raise BiliVideoIdException('bvid 格式不正确: bvid 必须是一个长度为12的字符串')
    if bvid[:2].upper() != 'BV':
        raise BiliVideoIdException('bvid 格式错误: bvid 必须是一个由BV开头的字符串')


def get_video_info(aid: int = None, bvid: str = None):
    api = copy.deepcopy(API['info'])
    url = urlsplit(api['url'])
    params: dict = api['params']
    if bvid is not None:
        __check_bvid(bvid)
        params.pop('aid')
        params['bvid'] = bvid
    elif aid is not None:
        params.pop('bvid')
        params['aid'] = aid
    else:
        raise BiliVideoIdException('你必须输入 aid, bvid 中的任意一个')

    get = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api['method'],
        path=url.path,
        query=params
    )
    if get['code'] != 0:
        raise NetWorkException('视频信息获取错误:\n{0};\n{1};\n{2}'.format(
            get['code'],
            api['return']['code'].get(str(get['code']), '未知错误'),
            get['message']
        ))
    return get['data']


def get_video_pages(aid: int = None, bvid: str = None):
    api = copy.deepcopy(API['pages'])
    url = urlsplit(api['url'])
    params: dict = api['params']
    if bvid is not None:
        __check_bvid(bvid)
        params.pop('aid')
        params['bvid'] = bvid
    elif aid is not None:
        params.pop('bvid')
        params['aid'] = aid
    else:
        raise BiliVideoIdException('你必须输入 aid, bvid 中的任意一个')

    get = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api['method'],
        path=url.path,
        query=params
    )
    if get['code'] != 0:
        raise NetWorkException('视频信息获取错误:\n{0};\n{1};\n{2}'.format(
            get['code'],
            api['return']['code'].get(str(get['code']), '未知错误'),
            get['message']
        ))
    return get['data']


def get_video_url(avid: int = None, bvid: str = None, cid: int = None, passport: utils.BiliPassport = None):
    if cid is None:
        raise BiliVideoIdException('你必须提供视频 cid')
    api = copy.deepcopy(API['get_download_url_wbi'])
    url = urlsplit(api['url'])
    params: dict = api['params']
    params.pop('qn')
    params.pop('fnver')
    params['cid'] = cid
    params['fnval'] = 16 | 128 | 2048  # Dash 4K AV1_Codec
    params['fourk'] = 1
    if bvid is not None:
        __check_bvid(bvid)
        params.pop('avid')
        params['bvid'] = bvid
    elif avid is not None:
        params.pop('bvid')
        params['avid'] = avid
    else:
        raise BiliVideoIdException('你必须输入 aid, bvid 中的任意一个')
    params = wbisign.sign_params(params, passport)
    header = {}
    if passport is not None:
        header['cookie'] = passport.get_cookie()
    get: dict = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api['method'],
        path=url.path,
        query=params,
        header=header
    )

    if get['code'] != 0:
        raise NetWorkException('视频链接获取错误:\n{0};\n{1};\n{2}'.format(
            get['code'],
            api['return']['code'].get(str(get['code']), '未知错误'),
            get['message']
        ))
    return get['data']


def get_video_online_count(cid: int, aid: int = None, bvid: str = None):
    api = copy.deepcopy(API['online_count'])
    url = urlsplit(api['url'])
    params: dict = api['params']
    params['cid'] = cid
    if bvid is not None:
        __check_bvid(bvid)
        params.pop('aid')
        params['bvid'] = bvid
    elif aid is not None:
        params.pop('bvid')
        params['aid'] = aid
    else:
        raise BiliVideoIdException('你必须输入 aid, bvid 中的任意一个')

    get: dict = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api['method'],
        path=url.path,
        query=params
    )

    if get['code'] != 0:
        raise NetWorkException('视频在线人数获取错误: {0}; {1}; {2}'.format(
            get['code'],
            api['return']['code'].get(str(get['code']), '未知错误'),
            get['message']
        ))

    return get['data']
