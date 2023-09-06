from bdnet import server
import threading as thr
import datetime
import time
import sys
import re


logcount = 0
logfile = None


def logstr(*st):
    sts = []
    for i in st:
        sts.append(str(i))
    ret = " ".join(sts)
    return ret


def log(s: str, level: str = "info"):
    global logcount
    if logcount == 0 or logcount > 10000:
        global logfile
        if logfile:
            logfile.close()
        logfile = open(
            "./logs/{}.log".format(
                datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            ),
            "w",
            buffering=1,
        )
        sys.stdout = logfile
        logcount = 0
    prstr = "[{}][{}] ".format(
        datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), level
    )
    prstr += s
    print(prstr)
    logcount += 1


class Runner(thr.Thread):
    def __init__(self, l):
        super().__init__()
        self._l: server.Linker = l

    def run(self):
        log("Linker: {}".format(self._l.getAddr()))
        try:
            get = self._l.recvMsg()
            log("Action: {}".format(get))
            if get["action"] == "version":
                if "after" in get:
                    self._l.sendMsg({"content": getVersionAfter()})
                else:
                    self._l.sendMsg({"content": getVersion()})
            elif get["action"] == "updateInfo":
                self._l.sendMsg({"content": getUpdateInfo()})
            elif get["action"] == "updateUrl":
                get_info = getUpdateUrl()
                self._l.sendMsg({"content": {"url": get_info[0], "hash": get_info[1]}})
            time.sleep(0.2)
            self._l.close()
        except:
            log(logstr(sys.exc_info()[0], sys.exc_info()[1]), "Exception")
            try:
                self._l.close()
            except:
                log("Close Error...", "Exception")


def getVersion():
    get = str()
    with open("./data/ver", "r") as f:
        get = f.read()
    return get


def getVersionAfter():
    get = str()
    with open("./data/ver", "r") as f:
        get = f.read()
    return get


def getUpdateInfo():
    get = str()
    with open("./data/updateInfo", "r", encoding="utf_8") as f:
        get = f.read()
    return get


def getUpdateUrl():
    get = list()
    with open("./data/updateUrl", "r") as f:
        get.append(f.read())
    with open("./data/updateHash", "r") as f:
        get.append(f.read())
    return tuple(get)


def main():
    ser = server.Server(11288)
    while True:
        try:
            l = ser.listen()
            run = Runner(l)
            run.start()
        except KeyboardInterrupt:
            global logfile
            log("stop...")
            if logfile:
                logfile.close()
            break
        except:
            log("Connection create error...", "Exception")


if __name__ == "__main__":
    main()
