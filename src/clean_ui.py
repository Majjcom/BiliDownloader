import os


def main():
    if not os.path.exists(".ui_compiled.cache"):
        print("Cache file not found...")
        return
    f = open(".ui_compiled.cache", "r")
    for line in f:
        filename = line.strip()
        if os.path.exists(filename):
            os.remove(filename)
            print("Cleaning", filename)
    f.close()
    os.remove(".ui_compiled.cache")


if __name__ == "__main__":
    main()
