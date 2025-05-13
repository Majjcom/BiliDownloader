import copy
import http.client
import json
import urllib.parse
from typing import Union

from ..exceptions.NetWorkException import NetWorkException

DEFAULT_HEADERS = {"Referer": "https://www.bilibili.com", "User-Agent": "Mozilla/5.0"}


def get_data(
        scheme: str,
        host: str,
        method: str,
        path: str,
        query: dict = None,
        header: dict = None,
):
    c = (
        http.client.HTTPSConnection(host)
        if scheme == "https"
        else http.client.HTTPConnection(host)
    )
    if method.upper() == "GET":
        qu = "" if query is None else "?{}".format(urllib.parse.urlencode(query))
    else:
        qu = urllib.parse.urlencode(query)
    head = copy.deepcopy(DEFAULT_HEADERS)
    if header is not None:
        for i in header:
            head[i] = header[i]
    if method == "GET":
        c.request(method, path + qu, headers=head)
    else:
        head["Content-Type"] = "application/x-www-form-urlencoded"
        c.request(method, path, body=qu, headers=head)
    r = c.getresponse()
    ret = json.loads(r.read())
    r.close()
    c.close()
    return ret


class DataGetter:
    def __init__(
            self,
            scheme: str,
            host: str,
            method: str,
            path: str,
            query: dict = None,
            header: dict = None,
    ):
        self._scheme = scheme
        self._host = host
        self._method = method
        self._path = path
        self._query = query
        self._header = header
        self._c: Union[http.client.HTTPConnection, http.client.HTTPSConnection] = None
        if method == "GET":
            self._qu = (
                ""
                if self._query is None
                else "?{}".format(urllib.parse.urlencode(self._query))
            )
        else:
            self._qu = urllib.parse.urlencode(self._query)
        self._head = copy.deepcopy(DEFAULT_HEADERS)
        if header is not None:
            for i in header:
                self._head[i] = header[i]
        self._linked = False

    def link(self):
        self._c = (
            http.client.HTTPSConnection(self._host)
            if self._scheme == "https"
            else http.client.HTTPConnection(self._host)
        )
        self._linked = True

    def request(self) -> dict:
        if not self._linked:
            raise NetWorkException("Not Linked...")
        if self._method == "GET":
            self._c.request(self._method, self._path + self._qu, headers=self._head)
        else:
            data = self._qu.encode("utf_8")
            self._head["Content-Type"] = "application/x-www-form-urlencoded"
            self._c.request(self._method, self._path, body=data, headers=self._head)
        r = self._c.getresponse()
        data = r.read()
        get = json.loads(data)
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
