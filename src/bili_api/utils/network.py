from ..exceptions.NetWorkException import NetWorkException
from typing import Union
import urllib.parse
import http.client
import json


DEFAULT_HEADERS = {"Referer": "https://www.bilibili.com",
                   "User-Agent": "Mozilla/5.0"}


def get_data(scheme: str, host: str, method: str, path: str, query: dict = None, header: dict = None):
    c = http.client.HTTPSConnection(host) if scheme == 'https' else http.client.HTTPConnection(host)
    qu = '' if query is None else '?{}'.format(urllib.parse.urlencode(query))
    head = DEFAULT_HEADERS
    if header is not None:
        for i in header:
            head[i] = header[i]
    c.request(method, path + qu, headers=head)
    r = c.getresponse()
    ret = json.loads(r.read())
    r.close()
    c.close()
    return ret


class Data_getter:
    def __init__(self, scheme: str, host: str, method: str, path: str, query: dict = None, header: dict = None):
        self._scheme = scheme
        self._host = host
        self._method = method
        self._path = path
        self._query = query
        self._header = header
        self._c: Union[http.client.HTTPConnection, http.client.HTTPSConnection] = None
        self._qu = '' if self._query is None else '?{}'.format(urllib.parse.urlencode(self._query))
        self._head = DEFAULT_HEADERS
        if header is not None:
            for i in header:
                self._head[i] = header[i]
        self._linked = False

    def link(self):
        self._c = http.client.HTTPSConnection(self._host) if self._scheme == 'https' else http.client.HTTPConnection(self._host)
        self._linked = True

    def request(self) -> dict:
        if not self._linked:
            raise NetWorkException('Not Linked...')
        self._c.request(self._method, self._path + self._qu, headers=self._head)
        r = self._c.getresponse()
        get = json.loads(r.read())
        r.close()
        return get

    def close(self):
        self._c.close()

    def __del__(self):
        if self._linked:
            self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
