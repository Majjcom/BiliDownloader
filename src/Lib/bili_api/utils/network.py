import copy
import gzip
import http.client
import json
import urllib.parse
import zlib
from typing import Union

import brotli
import zstandard

from .defaultHeaders import DEFAULT_HEADERS
from ..exceptions.NetWorkException import NetWorkException


def get_data(
        scheme: str,
        host: str,
        method: str,
        path: str,
        query: dict = None,
        header: dict = None,
        data=None,
        data_type: str = "application/json"
):
    c = (
        http.client.HTTPSConnection(host)
        if scheme == "https"
        else http.client.HTTPConnection(host)
    )
    if query is not None:
        if len(query) == 0:
            query = None
    qu = "" if query is None else "?{}".format(urllib.parse.urlencode(query))
    head = copy.deepcopy(DEFAULT_HEADERS)
    if header is not None:
        for i in header:
            head[i] = header[i]
    if method == "GET":
        c.request(method, path + qu, headers=head)
    else:
        if isinstance(data, dict):
            if data_type == "application/x-www-form-urlencoded":
                qdata = urllib.parse.urlencode(data).encode("utf-8")
            else:
                qdata = json.dumps(data, separators=(',', ':')).encode("utf-8")
        else:
            qdata = data
        head["Content-Type"] = data_type
        c.request(method, path + qu, body=qdata, headers=head)
    r = c.getresponse()
    encoding = r.headers.get("Content-Encoding")
    read_data = r.read()
    if encoding is not None:
        if encoding == "gzip":
            dec = gzip.decompress(read_data)
        elif encoding == "deflate":
            dec = zlib.decompress(read_data, -zlib.MAX_WBITS)
        elif encoding == "br":
            dec = brotli.decompress(read_data)
        elif encoding == "zstd":
            dec = zstandard.decompress(read_data)
        else:
            dec = read_data
    else:
        dec = read_data
    ret = json.loads(dec)
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
        encoding = r.headers.get("Content-Encoding")
        if encoding is not None:
            if encoding == "gzip":
                data = gzip.decompress(data)
            elif encoding == "deflate":
                data = zlib.decompress(data, -zlib.MAX_WBITS)
            elif encoding == "br":
                data = brotli.decompress(data)
            elif encoding == "zstd":
                data = zstandard.decompress(data)
        data = data.decode("utf-8")
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
