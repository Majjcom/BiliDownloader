def sizefStr(size: int):
    SStr = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    for i in range(len(SStr) - 1):
        if size // 1024 ** (i + 1):
            continue
        break
    return str(round(size / 1024 ** i, 2)) + SStr[i]
