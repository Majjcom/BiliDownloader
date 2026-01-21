__version__ = "1.3.18"


def check_version(new: str, old: str) -> bool:
    new = new.split(".")
    old = old.split(".")
    for i in range(len(new)):
        if int(new[i]) > int(old[i]):
            return True
        elif int(new[i]) == int(old[i]):
            continue
        else:
            return False
    return False


def check_update(new: str):
    return check_version(new, __version__)


if __name__ == "__main__":
    print(check_version("1.0.0", "0.0.1"))
    print(check_version("1.0.1", "1.0.0"))
    print(check_version("1.0.1", "1.0.1"))
    print(check_version("1.0.1", "1.0.2"))
    print(check_version("0.13.0", "1.0.0"))
