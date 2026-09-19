import copy
import http.client
import zlib
from urllib.parse import urlencode
from urllib.parse import urlsplit

from . import utils

API = utils.get_api(('danmaku',))
_NETWORK_TIMEOUT = 15


def get_danmaku_xml(cid: int) -> str:
    api = copy.deepcopy(API['xml'])
    url = urlsplit(api['url'])
    params = api['params']
    params['oid'] = cid
    qu = '?' + urlencode(params)
    conn = (
        http.client.HTTPConnection(url.netloc, timeout=_NETWORK_TIMEOUT)
        if url.scheme == 'http'
        else http.client.HTTPSConnection(url.netloc, timeout=_NETWORK_TIMEOUT)
    )
    get = None
    try:
        conn.request(
            method=api['method'],
            url=url.path + qu
        )
        get = conn.getresponse()
        data_compressed = get.read()
    finally:
        if get is not None:
            get.close()
        conn.close()
    data = zlib.decompress(data_compressed, -zlib.MAX_WBITS)
    return data.decode('utf_8')
