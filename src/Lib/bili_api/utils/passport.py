import base64
import json
import uuid

from Crypto.Cipher import AES

from .cookieTools import make_cookie

__all__ = ['BiliPassport', 'encode_cookie', 'decode_cookie']


def encode_cookie(data):
    s = json.dumps(data).encode('utf_8')
    hardware_addr = uuid.getnode().to_bytes(6, "big")
    cipher = AES.new((hardware_addr * 3)[:16], AES.MODE_ECB)
    pad = 16 - len(s) % 16
    s = bytearray(s)
    for _ in range(pad):
        s.append(pad)
    crypted = cipher.encrypt(s)
    return base64.b64encode(crypted).decode("utf_8")


def decode_cookie(data):
    try:
        bs = base64.b64decode(data)
        hardware_addr = uuid.getnode().to_bytes(6, "big")
        cipher = AES.new((hardware_addr * 3)[:16], AES.MODE_ECB)
        plain = cipher.decrypt(bs)
        plain = plain[:-plain[-1]]
        return json.loads(plain.decode('utf_8'))
    except Exception as _:
        return None


class BiliPassport:
    def __init__(self, raw: dict):
        self._raw = raw

    def get_cookie(self):
        return make_cookie(self._raw)
