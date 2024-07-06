import os
import subprocess

dirs = os.listdir(".")

f = open(".ui_compiled.cache", "w")

for i in dirs:
    if i.endswith(".ui"):
        tgt = i[:-3] + ".py"
        f.write(tgt + "\n")
        print(i + " => " + tgt)
        subprocess.call(["pyside6-uic", i, "-o", tgt])
    if i.endswith(".qrc"):
        tgt = i[:-4] + "_rc.py"
        f.write(tgt + "\n")
        print(i + " => " + tgt)
        subprocess.call(["pyside6-rcc", i, "-o", tgt])

f.close()
