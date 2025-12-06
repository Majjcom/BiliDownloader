import copy
import http.client
import urllib.parse

from .defaultHeaders import DEFAULT_HEADERS


def load_bili_image(url: str):
    urlinfo = urllib.parse.urlparse(url)
    c = http.client.HTTPConnection(urlinfo.netloc) \
        if urlinfo.scheme == "http" \
        else http.client.HTTPSConnection(urlinfo.netloc)
    header = copy.deepcopy(DEFAULT_HEADERS)
    header.pop("Accept-Encoding")
    c.request("GET", urlinfo.path, headers=header)
    resp = c.getresponse()
    return resp.read()
