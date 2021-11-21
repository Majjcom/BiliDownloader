from bdnet import server
import threading as thr
import datetime
import time
import sys


class Runner(thr.Thread):
    def __init__(self, addr):
        thr.Thread.__init__(self)
        self._addr = addr

    def run(self):
        print('[{}] Linker: {}'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'), self._addr[1]))
        get = server.recvMsg(self._addr[0], self._addr[2])
        print('[{}] Action: {}'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'), get))
        if get['action'] == 'version':
            server.sendMsg(self._addr[0], {'content': getVersion()},self._addr[2])
        elif get['action'] == 'downloadUrl':
            server.sendMsg(self._addr[0], {'content': getDownloadUrl()}, self._addr[2])
        time.sleep(0.2)
        server.close(self._addr[0])


def getVersion():
    get = str()
    with open('./data/ver', 'r') as f:
        get = f.read()
    return get


def getDownloadUrl():
    get = str()
    with open('./data/url', 'r') as f:
        get = f.read()
    return get


def main():
    log = open(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.log'), 'w', buffering=1)
    sys.stdout = log
    sock = server.create(11288)
    while True:
        addr = server.listen(sock)
        run = Runner(addr)
        run.start()


if __name__ == '__main__':
    main()
