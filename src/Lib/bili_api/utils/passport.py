from .cookieTools import make_cookie


class BiliPassport:
    def __init__(self, raw: dict):
        self._raw = raw

    def get_cookie(self):
        return make_cookie(self._raw)
