from urllib.parse import urlsplit
from . import utils


API = utils.get_api(('user',))


def get_login_url():
    api = API['get_login_url']
    url = urlsplit(api['url'])
    params = api['params']
    get = utils.network.get_data(
        scheme=url.scheme,
        host=url.netloc,
        method=api['method'],
        path=url.path,
    )
    return {'ts': get['ts'], 'data': get['data']}


class Get_login_info(utils.network.Data_getter):
    def __init__(self, oauthKey: str):
        api = API['get_login_data']
        url = urlsplit(api['url'])
        params = api['params']
        params.pop('gourl')
        params['oauthKey'] = oauthKey
        super().__init__(
            scheme=url.scheme,
            host=url.netloc,
            method=api['method'],
            path=url.path,
            query=params
        )
        self.link()
