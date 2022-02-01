import json
import os


def get_api(li: tuple) -> dict:
    with open(os.path.join(os.path.split(__file__)[0], 'data/api.json'), encoding='utf-8') as f:
        ret = json.load(f)
        for i in li:
            ret = ret[i]
    return ret

