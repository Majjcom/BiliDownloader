import json
import os


def get_api(li: tuple) -> dict:
    li = list(li)
    with open(os.path.join(os.path.split(__file__)[0], 'data/{}.json'.format(li[0])), encoding='utf-8') as f:
        ret = json.load(f)
        li.pop(0)
        for i in li:
            ret = ret[i]
    return ret

