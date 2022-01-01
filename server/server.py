from bdnet import server
import threading as thr
import datetime
import time
import sys


class Runner(thr.Thread):
    def __init__(self, l):
        super().__init__()
        self._l: server.Linker = l

    def run(self):
        try:
            print('[{}] Linker: {}'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'), self._l.getAddr()))
            get = self._l.recvMsg()
            print('[{}] Action: {}'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'), get))
            if get['action'] == 'version':
                if 'after' in get:
                    self._l.sendMsg({'content': getVersionAfter()})
                else:
                    self._l.sendMsg({'content': getVersion()})
            elif get['action'] == 'updateInfo':
                self._l.sendMsg({'content': getUpdateInfo()})
            elif get['action'] == 'updateUrl':
                get_info = getUpdateUrl()
                self._l.sendMsg({'content': {'url': get_info[0], 'hash': get_info[1]}})
            time.sleep(0.2)
            self._l.close()
        except:
            print('[Expection][{}]'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')), sys.exc_info()[0], sys.exc_info()[1])
            try:
                self._l.close()
            except:
                print('[Expection][{}]'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')), 'Close Error...')


def getVersion():
    get = str()
    with open('./data/ver', 'r') as f:
        get = f.read()
    return get

def getVersionAfter():
    get = str()
    with open('./data/ver', 'r') as f:
        get = f.read()
    return get

def getUpdateInfo():
    get = str()
    with open('./data/updateInfo', 'r') as f:
        get = f.read()
    g = get.split('\n-')
    ret = g[0] + '\n-' + g[1]
    return ret


def getUpdateUrl():
    get = list()
    with open('./data/updateUrl', 'r') as f:
        get.append(f.read())
    with open('./data/updateHash', 'r') as f:
        get.append(f.read())
    return tuple(get)


def main():
    log = open('./logs/{}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')), 'w', buffering=1)
    sys.stdout = log
    ser = server.Server(11288)
    while True:
        try:
            l = ser.listen()
            run = Runner(l)
            run.start()
        except:
            print('[Expection][{}]'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')), sys.exc_info()[0], sys.exc_info()[1])


if __name__ == '__main__':
    main()
