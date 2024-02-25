import json as _json
import socket as _socket
from hashlib import sha256 as _sha256
from random import randint as _randint

from Crypto.Cipher import AES as _AES

from .rconn_client import rconn as _rconn
from .const import CONST_KEY as _CONST_KEY


class BDClient:
    def __init__(self, host: str, port: int):
        addr = _socket.gethostbyname(host)
        self._c = _rconn.RconnClient((addr, port))
        self._c.settimeout(3)

    def request(self, data: dict):
        key = _gen_key()
        hasher = _sha256()
        hasher.update(key.encode("ascii"))
        hasher.update(_CONST_KEY)
        hash_data = hasher.hexdigest().lower()
        ikey = hash_data[2:18].encode("ascii")
        nonce = hash_data[6:18].encode("ascii")
        chiper = _AES.new(key=ikey, mode=_AES.MODE_GCM, nonce=nonce)
        rdata = _json.dumps(data)
        (en_data, tag) = chiper.encrypt_and_digest(rdata.encode("utf_8"))
        en_data += tag
        resp = self._c.request(_rconn.RconnData("any", {"key": key}, en_data))
        key = resp.data["key"]
        hasher = _sha256()
        hasher.update(key.encode("ascii"))
        hasher.update(_CONST_KEY)
        hash_data = hasher.hexdigest().lower()
        ikey = hash_data[2:18].encode("ascii")
        nonce = hash_data[6:18].encode("ascii")
        chiper = _AES.new(key=ikey, mode=_AES.MODE_GCM, nonce=nonce)
        rdata = resp.custom_data[:-16]
        tag = resp.custom_data[-16:]
        de_data = chiper.decrypt_and_verify(rdata, tag)
        return _json.loads(de_data)

    def close(self):
        self._c.close()


def _gen_key() -> str:
    return "".join([chr(_randint(65, 65 + 25)) for _ in range(32)])
