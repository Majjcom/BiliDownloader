from ..exceptions.BiliVideoIdException import BiliVideoIdException


def check_bvid(bvid: str) -> None:
    if len(bvid) != 12:
        raise BiliVideoIdException('bvid 格式不正确: bvid 必须是一个长度为12的字符串')
    if bvid[:2].upper() != 'BV':
        raise BiliVideoIdException('bvid 格式错误: bvid 必须是一个由BV开头的字符串')
