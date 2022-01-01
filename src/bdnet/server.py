# Copyright (c) 2021 Majjcom
from .utils import scode
import socket
import time
import json


class BasicConnection:
    
    def __init__(self) -> None:
        self._s: socket.SocketType = None
        pass
    

    def _recvBuff(self, timeout: float = 10.0) -> bytes:
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
    

    def close(self):
        self._s.close()


class Server(BasicConnection):

    def __init__(self, port: int) -> None:
        super().__init__()
        self._port = port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s = s
        addr = ('0.0.0.0', port)
        self._s.bind(addr)
        self._s.listen(5)
        
    
    def listen(self):
        l, l_addr = self._s.accept()
        return Linker(l, l_addr)


class Linker(BasicConnection):

    def __init__(self, s: socket.SocketType, addr: tuple) -> None:
        super().__init__()
        self._s = s
        self._addr = addr
        self._s.settimeout(10)
        key = scode.getRandKey(16)
        self._key = key
        post = {'key': key}
        msg = json.dumps(post).encode('utf-8')
        self._s.sendall(msg + '@@$'.encode('utf-8'))
        get = json.loads(self._recvBuff(3.0).decode('utf-8'))
        if get['result'] != 'ok':
            raise

    
    def recvMsg(self):
        get = self._recvBuff(5.0)
        ret = json.loads(scode.decode(self._key, get).decode('utf-8'))
        post = {'result': 'ok'}
        self._s.sendall(scode.encode(self._key, json.dumps(post).encode('utf-8')) + '@@$'.encode('utf-8'))
        return ret
    

    def sendMsg(self, content: dict):
        msg = scode.encode(self._key, json.dumps(content).encode('utf-8'))
        self._s.sendall(msg + '@@$'.encode('utf-8'))
        get = json.loads(scode.decode(self._key, self._recvBuff(3.0)).decode('utf-8'))
        if get is None:
            return False
        if get['result'] == 'ok':
            return True
        return False
    

    def getAddr(self):
        return self._addr
