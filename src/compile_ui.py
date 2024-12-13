import os
import subprocess

from Crypto.Hash import SHA256


def check_cache(cache, tgt, hashhex):
    if cache is None:
        return False
    if tgt in cache:
        if hashhex == cache[tgt]:
            return True
    return False


def main():
    dirs = os.listdir(".")
    cache: dict | None = None

    if os.path.exists(".ui_compiled.cache"):
        cache = {}
        with open(".ui_compiled.cache", "r") as cache_file:
            print("Reading cache")
            for line in cache_file:
                linestrip = line.strip()
                name = linestrip.split(" ")[0]
                hashhex = linestrip.split(" ")[1]
                cache[name] = hashhex

    f = open(".ui_compiled.cache", "w")

    for i in dirs:
        if i.endswith(".ui"):
            with open(i, "rb") as fc:
                hashhex = SHA256.new(fc.read()).hexdigest()
            tgt = i[:-3] + ".py"
            if check_cache(cache, tgt, hashhex):
                print("cache => {}".format(tgt))
                f.write(tgt + " " + hashhex + "\n")
                cache.pop(tgt)
                continue
            f.write(tgt + " " + hashhex + "\n")
            print(i + " => " + tgt)
            subprocess.call(["pyside6-uic", i, "-o", tgt])
        if i.endswith(".qrc"):
            with open(i, "rb") as fc:
                hashhex = SHA256.new(fc.read()).hexdigest()
            tgt = i[:-4] + "_rc.py"
            if check_cache(cache, tgt, hashhex):
                print("cache => {}".format(tgt))
                f.write(tgt + " " + hashhex + "\n")
                cache.pop(tgt)
                continue
            f.write(tgt + " " + hashhex + "\n")
            print(i + " => " + tgt)
            subprocess.call(["pyside6-rcc", i, "-o", tgt])

    if cache:
        for k, v in cache.items():
            f.write(k + " " + v + "\n")

    f.close()


if __name__ == "__main__":
    main()
