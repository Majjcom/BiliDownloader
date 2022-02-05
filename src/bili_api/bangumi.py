from .exceptions.BiliVideoIdException import BiliVideoIdException
from .exceptions.NetWorkException import NetWorkException
from urllib.parse import urlsplit
from . import utils
import copy


API = utils.get_api(('bangumi',))


def get_bangumi_info(media_id: int):
    api = copy.deepcopy(API['info'])
    url = urlsplit(api['url'])
    params = api['params']
    params['media_id'] = media_id

    get = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api['method'],
        path=url.path,
        query=params
    )
    if get['code'] != 0:
        raise NetWorkException('番剧信息获取错误: {0}; {1}; {2}'.format(
            get['code'],
            api['return']['code'].get(str(get['code']), '未知错误'),
            get['message']
        ))
    return get['result']


def get_bangumi_detailed_info(season_id: int=None, ep_id: int=None, media_id: int=None):
    api = copy.deepcopy(API['detailed_info'])
    url = urlsplit(api['url'])
    params = api['params']
    if media_id is not None and season_id is None and ep_id is None:
        info = get_bangumi_info(media_id)
        season_id = info['media']['season_id']
    if season_id is not None:
        params.pop('ep_id')
        params['season_id'] = season_id
    elif ep_id is not None:
        params.pop('season_id')
        params['ep_id'] = ep_id
    else:
        raise BiliVideoIdException('你必须提供 season_id 和 ep_id 中的任意一个')

    get = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api['method'],
        path=url.path,
        query=params
    )
    if get['code'] != 0:
        raise NetWorkException('番剧详细信息获取错误: {0}; {1}; {2}'.format(
            get['code'],
            api['return']['code'].get(str(get['code']), '未知错误'),
            get['message']
        ))
    info = get_bangumi_info(get['result']['media_id']) if media_id is None else info
    return {'info': info, 'data': get['result']}
