from urllib.parse import urlencode
from urllib.parse import urlsplit
from . import utils
import http.client
import zlib
import copy


API = utils.get_api(('danmaku', ))


def get_danmaku_xml(cid: int) -> str:
    api = copy.deepcopy(API['xml'])
    url = urlsplit(api['url'])
    params = api['params']
    params['oid'] = cid
    qu = '?' + urlencode(params)
    conn = http.client.HTTPConnection(url.netloc) if url.scheme == 'http' else http.client.HTTPSConnection(url.netloc)
    conn.request(
        method=api['method'],
        url=url.path + qu
    )
    get = conn.getresponse()
    data_compressed = get.read()
    get.close()
    conn.close()
    data = zlib.decompress(data_compressed, -zlib.MAX_WBITS)
    return data.decode('utf_8')
