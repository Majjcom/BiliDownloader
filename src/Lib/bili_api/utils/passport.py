import base64
import json
import random
import sys

from Crypto.Cipher import AES

from .cookieTools import make_cookie

__all__ = ['BiliPassport', 'encode_cookie', 'decode_cookie', 'gen_key', 'get_key']


def gen_key():
    r = random.SystemRandom()
    k = r.randbytes(16)
    if sys.platform == "win32":
        import win32crypt
        k = win32crypt.CryptProtectData(k, None, None, None, None, 0)
    return base64.b64encode(k).decode("utf_8")


def get_key(data):
    r = base64.b64decode(data.encode('utf_8'))
    if sys.platform == "win32":
        import win32crypt
        r = win32crypt.CryptUnprotectData(r, None, None, None, 0)[1]
    return r


def encode_cookie(data, key):
    s = json.dumps(data).encode('utf_8')
    cipher = AES.new(get_key(key), AES.MODE_ECB)
    pad = 16 - len(s) % 16
    s = bytearray(s)
    for _ in range(pad):
        s.append(pad)
    crypted = cipher.encrypt(s)
    return base64.b64encode(crypted).decode("utf_8")


def decode_cookie(data, key):
    try:
        bs = base64.b64decode(data)
        cipher = AES.new(get_key(key), AES.MODE_ECB)
        plain = cipher.decrypt(bs)
        plain = plain[:-plain[-1]]
        return json.loads(plain.decode('utf_8'))
    except Exception as e:
        return None


class BiliPassport:
    def __init__(self, raw: dict):
        self._raw = raw

    def get_data(self):
        return self._raw

    def get_cookie(self):
        return make_cookie(self._raw)
