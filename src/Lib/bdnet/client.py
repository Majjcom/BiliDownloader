# Copyright (c) 2021 Majjcom
from .utils import scode
import socket
import time
import json


class Connection:

    def __init__(self, ip: str, port: int):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((socket.gethostbyname(ip), port))
        s.settimeout(5)
        self._s = s
        get = json.loads(self._recvBuff(5.0).decode('utf-8'))
        key = get['key']
        post = {'result': 'ok'}
        self._s.sendall(json.dumps(post).encode('utf-8') + '@@$'.encode('utf-8'))
        self._key = key
    
    
    def recvMsg(self) -> dict:
        get = self._recvBuff(5.0)
        ret = json.loads(scode.decode(self._key, get).decode('utf-8'))
        post = {'result': 'ok'}
        self._s.sendall(scode.encode(self._key, json.dumps(post).encode('utf-8')) + '@@$'.encode('utf-8'))
        return ret
    
    
    def sendMsg(self, content: dict) -> bool:
        msg = scode.encode(self._key, json.dumps(content).encode('utf-8'))
        self._s.sendall(msg + '@@$'.encode('utf-8'))
        get = json.loads(scode.decode(self._key, self._recvBuff(5.0)).decode('utf-8'))
        if get is None:
            return False
        if get['result'] == 'ok':
            return True
        return False
    
    
    def _recvBuff(self, timeout: float) -> bytes:
        t0 = time.time()
        buff = bytes()
        while True:
            tmp = self._s.recv(1024)
            if len(tmp) != 0:
                buff += tmp
                break
            if time.time() - t0 > timeout:
                raise
        while len(tmp) == 1024:
            if tmp[-3:0] == '@@$'.encode('utf-8'):
                break
            tmp = self._s.recv(1024)
            buff += tmp
        return buff[:len(buff) - 3]


    def close(self) -> None:
        self._s.close()
        return
