import subprocess
import os

dirs = os.listdir(".")

for i in dirs:
    if i.endswith(".ui"):
        tgt = i[:-3] + ".py"
        print(i + " => " + tgt)
        subprocess.call(["pyside2-uic", i, "-o", tgt])

for i in dirs:
    if i.endswith(".qrc"):
        tgt = i[:-4] + "_rc.py"
        print(i + " => " + tgt)
        subprocess.call(["pyside2-rcc", i, "-o", tgt])
