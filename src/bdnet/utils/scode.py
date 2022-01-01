import itertools
import hashlib
import random
import time

constKey = 'bilidown.bdnet.Majjcom.site'

def encode(key: str, content: bytes) -> bytes:
    key_a = hashlib.sha256((constKey + key).encode('utf-8')).hexdigest()
    con_a = key_a.encode('utf-8') + content
    ran = random.Random()
    ran.seed(key_a, version=2)
    key_s = str()
    for i in range(128):
        key_s += chr(ran.randint(44, 122))
    length, key_l, key_iter = len(con_a), str(), itertools.cycle(key_s)
    for i in range(length):
        key_l += next(key_iter)
    con_i = int.from_bytes(con_a, 'big')
    key_i = int.from_bytes(key_l.encode('utf-8'), 'big')
    res_b = int.to_bytes(con_i ^ key_i, length, 'big')
    return res_b


def decode(key: str, content: bytes) -> bytes:
    key_a = hashlib.sha256((constKey + key).encode('utf-8')).hexdigest()
    ran = random.Random()
    ran.seed(key_a, version=2)
    key_s = str()
    for i in range(128):
        key_s += chr(ran.randint(44, 122))
    length, key_l, key_iter = len(content), str(), itertools.cycle(key_s)
    for i in range(length):
        key_l += next(key_iter)
    con_i = int.from_bytes(content, 'big')
    key_i = int.from_bytes(key_l.encode('utf-8'), 'big')
    res_b = int.to_bytes(con_i ^ key_i, length, 'big')
    if res_b[:len(key_a)] != key_a.encode('utf-8'):
        return None
    return res_b[len(key_a):]


def getRandKey(length: int = 16) -> str:
    ret = str()
    ran = random.Random()
    ran.seed(str(time.time()))
    for i in range(length):
        ret += chr(ran.randint(44, 122))
    return ret
