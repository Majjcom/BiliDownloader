# Copyright (c) 2023 Majjcom
# BiliDownloader
# With MIT License
from bili_api.utils import BiliPassport, cookieTools, matchFomat
from bili_api import exceptions
from threading import Event
from bdnet import client
from window import *
import subprocess
import threadDown
import traceback
import bili_api
import aiohttp
import asyncio
import hashlib
import xml2ass
import qrcode
import json
import time
import sys
import os

class ErrorCountsTooMuch(Exception):
    def __init__(self, info : str = None):
        Exception.__init__(self)
        self.info : str = info
    def __str__(self):
        return self.info

class ErrorDownloadHash(Exception):
    def __init__(self, info : str = None):
        Exception.__init__(self)
        self.info = info
    def __str__(self):
        return self.info


class ErrorCredential(Exception):
    def __init__(self, info : str = None):
        Exception.__init__(self)
        self.info = info
    def __str__(self):
        return self.info


class ErrorGetVidioUrl(Exception):
    def __init__(self, info : str = None):
        Exception.__init__(self)
        self.info = info
    def __str__(self):
        return self.info


def removeSpecialCharacter(original: str) -> str:
    spe = ':~!@#$%^&*()+-*/<>,.[]\\|\"\' '
    ret = original[:]
    for ch in spe:
        ret = ret.replace(ch, '_')
    return ret


def downloadDanmaku(path: str, cid: int) -> None:
    danmakuXml = bili_api.danmaku.get_danmaku_xml(cid)
    danmakuAss = xml2ass.convertMain(danmakuXml, 852, 480, text_opacity=0.6)
    with open(path, 'w', encoding='utf_8') as f:
        f.write(danmakuAss)
    return


async def downloadVideo(Url: dict, qid: int, codec: int, v, name: str = 'video'):
    global mainprocess, programPath
    video_urls: list = Url['dash']['video']
    video_urls.sort(key=lambda x: x['id'], reverse=True)
    if qid > video_urls[0]['id']:
        qid = video_urls[0]['id']
    qid_match = []
    for i in video_urls:
        if i['id'] == qid:
            qid_match.append(i)
    qid_match.sort(key=lambda x: x['codecid'])
    video_url = qid_match[0]['baseUrl']
    for i in qid_match:
        if i['codecid'] == codec:
            video_url = i['baseUrl']

    HEADERS = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.bilibili.com/'
    }
    await threadDown.download_with_threads(video_url, v, '{}_temp.mp4'.format(name), headers=HEADERS, piece_per_size=(32 * 1024 ** 2))


async def downloadAudio(Url : dict, id : int, v, name : str = 'audio'):
    global mainprocess
    audio_url = Url['dash']['audio'][0]['baseUrl']
    HEADERS = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.bilibili.com/'
    }
    await threadDown.download_with_threads(audio_url, v, '{}_temp.m4a'.format(name), headers=HEADERS, piece_per_size=(16 * 1024 ** 2))


async def checkUpdate():
    global ver
    c = client.Connection('www.majjcom.site', 11288)
    c.sendMsg({'action': 'version', 'after': True, 'bVersion': ver})
    get = c.recvMsg()
    c.close()
    return get['content']


def ifuptodate(now: str, get: str) -> bool:
    a_s = now.split('.')
    b_s = get.split('.')
    for i in range(3):
        if int(a_s[i]) > int(b_s[i]):
            return True
        elif int(a_s[i]) == int(b_s[i]):
            continue
        else:
            return False
    return True


async def getUpdate(ver):
    name = f'BiliDownloader{ver}_Installer.exe'
    info = getUpdateUrl()
    url = info[0]
    realHash = info[1]
    arg : list = list()
    arg.append(False)
    win = window_updating(arg)
    win.start()
    time.sleep(0.5)
    if not os.path.exists(name):
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                length = int(resp.headers.get('content-length'))
                with open(name, 'w+b') as f:
                    process = 0
                    count = 0
                    while True:
                        chunk = await resp.content.read(1024)
                        process += len(chunk)
                        count += 1
                        if not chunk:
                            arg[1].set(100.0)
                            f.close()
                            await sess.close()
                            break
                        if count % 512 == 0:
                            arg[1].set(round(process / length * 100, 2))
                        f.write(chunk)
    fileHash = getFileHash(name)
    if fileHash.lower() != realHash.lower():
        if os.path.exists(name):
            os.remove(name)
        raise ErrorDownloadHash('文件下载不完整...')
    arg[0] = True
    time.sleep(0.3)
    os.system(name)
    time.sleep(0.2)
    global PID
    os.kill(PID, 9)


def getUpdateUrl():
    global ver
    s = client.Connection('www.majjcom.site', 11288)
    s.sendMsg({'action': 'updateUrl', 'bVersion': ver})
    get = s.recvMsg()
    s.close()
    return get['content']['url'], get['content']['hash']


def getUpdateInfo():
    s = client.Connection('www.majjcom.site', 11288)
    s.sendMsg({'action': 'updateInfo', 'bVersion': ver})
    get = s.recvMsg()
    s.close()
    return get['content']


def getFileHash(name):
    f = open(name, 'rb')
    Md5_buffer = hashlib.md5()
    for buff in iter(lambda: f.read(1024), b''):
        Md5_buffer.update(buff)
    f.close()
    return Md5_buffer.hexdigest()


def setupUserData(reset: bool = False) -> None:
    global programPath
    global ver
    if not os.path.exists(os.path.join(programPath, 'data')):
        os.mkdir(os.path.join(programPath, 'data'))
    if not os.path.exists(os.path.join(programPath, 'data/userdata.json')):
        with open(os.path.join(programPath, 'data/userdata.json'), 'w') as f:
            meta = {
                'version': ver,
                'isnew': False if reset else True,
                'userinfo': dict()
            }
            json.dump(meta, f, sort_keys=True, indent=2)


def getUserData(key : str):
    global programPath
    keywd = ('version', 'isnew')
    setupUserData()
    with open(os.path.join(programPath, 'data/userdata.json'), 'r') as f:
        userdata = json.load(f)
    if key in keywd:
        return userdata[key]
    if key in userdata['userinfo']:
        return userdata['userinfo'][key]
    return None


def setUserData(key : str, value : {dict, list, int, float, str}) -> bool:
    global programPath
    keywd = ('version', 'isnew')
    setupUserData()
    with open(os.path.join(programPath, 'data/userdata.json'), 'r') as f:
        userdata = json.load(f)
    if key in keywd:
        userdata[key] = value
    else:
        userdata['userinfo'][key] = value
    with open(os.path.join(programPath, 'data/userdata.json'), 'w') as f:
        json.dump(userdata, f, sort_keys=True, indent=2)
    return True


def reSetUserData():
    global programPath
    setupUserData()
    os.remove(os.path.join(programPath, 'data/userdata.json'))
    setupUserData(reset=True)


def removeUserData(key: str):
    global programPath
    setupUserData()
    with open(os.path.join(programPath, 'data/userdata.json'), 'r') as f:
        userdata: dict = json.load(f)
    if key in userdata['userinfo'].keys():
        userdata['userinfo'].pop(key)
    with open(os.path.join(programPath, 'data/userdata.json'), 'w') as f:
        json.dump(userdata, f, sort_keys=True, indent=2)
    return


def showUpdateInfo(VER : str):
    global programPath
    try:
        new_user = getUserData('isnew')
        ver_get = getUserData('version')
        if not ifuptodate(ver_get, VER):
            new_user = True
            setUserData('version', VER)
        if new_user:
            setUserData('isnew', False)
            os.startfile(os.path.realpath(os.path.join(programPath, 'src/CHANGELOG.txt')))
    except:
        raise
    finally:
        del new_user


def user_login():
    try:
        img_path = os.path.join(programPath, 'data/qrcode' + str(int(time.time())) + '.png')
        login_info = bili_api.user.get_login_url()
        qr = qrcode.QRCode()
        qr.add_data(login_info['data']['url'])
        qr.make()
        img = qr.make_image()
        with open(img_path, 'wb') as f:
            img.save(f)
        del qr, img
        e0, e1, e2, e3 = Event(), Event(), Event(), Event()
        Window_login(img_path, e0, e1, e2, e3).start()
        ret = None
        with bili_api.user.Get_login_info(login_info['data']['oauthKey']) as getter:
            while True:
                tmp = getter.request()
                if tmp.get('code', 0) != 0:
                    break
                if tmp['status']:
                    e1.set()
                    ret = {'ts': login_info['ts'], 'data': cookieTools.get_cookie(tmp['data']['url'])}
                    break
                elif e3.is_set():
                    break
                else:
                    if tmp['data'] < -4:
                        e0.set()
                    elif 0 > tmp['data'] > -3:
                        e2.set()
                        break
                time.sleep(0.5)
        return ret
    except:
        return None
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


async def videoDown(vid_id: str, passport: BiliPassport = None):
    global programPath
    isReserveAudio: Union[None, bool] = getUserData('reserveAudio')
    if isReserveAudio is None:
        isReserveAudio = False
    vid_id_isBV : bool = None
    if len(vid_id) <= 2:
        pass
    elif vid_id[:2].lower() == 'bv':
        vid_id_isBV = True
    elif vid_id[:2].lower() == 'av':
        vid_id_isBV = False
    if vid_id_isBV:
        vid_ID = vid_id
    else:
        vid_ID = int(vid_id[2:])
    vid_info = None
    online_count = None
    if vid_id_isBV:
        vid_info = bili_api.video.get_video_info(bvid=vid_ID)
        online_count = bili_api.video.get_video_online_count(vid_info['cid'], bvid=vid_ID)
    else:
        vid_info = bili_api.video.get_video_info(aid=vid_ID)
        online_count = bili_api.video.get_video_online_count(vid_info['cid'], aid=vid_ID)
    vid_pages = vid_info['pages']
    tmp = await window_confirm(
        '请确认视频:\n\n下载位置: {}\n标题: {}\nUP主: {}\n当前在线: {}'.format(
            getUserData('downloadPath'),
            vid_info['title'],
            vid_info['owner']['name'],
            online_count['total']
        ),
        vid_info['pic']
    )
    if not tmp:
        await window_warn('退出...', playSound=False, level='信息')
        return
    vid_pages_count : int = len(vid_pages)
    while True:
        vid_chose : str = await window_config_p(vid_pages_count)
        vid_chose = vid_chose.replace(' ', '')
        try:
            vid_chose_a = vid_chose.split(',')
            vid_chose_b : list = []
            for i in vid_chose_a:
                vid_chose_b.append(i.split('-'))
            vid_chose_c : dict = {}
            for i in vid_chose_b:
                if int(i[0]) > int(i[1]):
                    raise
                if int(i[1]) > vid_pages_count:
                    raise
                tmp = list(range(int(i[0]) - 1, int(i[1])))
                for j in tmp:
                    vid_chose_c[vid_pages[j]['cid']] = {'page': vid_pages[j]['page'], 'part': vid_pages[j]['part']}
            break
        except:
            await window_warn('请输入正确的值...')
    urls : list = list()
    arg = list()
    arg.append(False)
    tmp = window_geturl(arg)
    tmp.start()
    time.sleep(0.5)
    for key in vid_chose_c:
        arg[1].set('正在获取 {} 的链接'.format(key))
        errtime = 0
        errinfo = None
        while True:
            try:
                if errtime > 5:
                    await window_warn("获取视频链接错误: {}".format(errinfo), level='错误')
                    return
                if vid_id_isBV:
                    url = bili_api.video.get_video_url(bvid=vid_ID, cid=key, passport=passport)
                else:
                    url = bili_api.video.get_video_url(avid=vid_ID, cid=key, passport=passport)
                break
            except:
                errtime += 1
                errinfo = traceback.format_exc()
                time.sleep(0.8)
        del errtime, errinfo
        data = {
            'name': 'p_{}_{}'.format(vid_chose_c[key]['page'], removeSpecialCharacter(vid_chose_c[key]['part'])),
            'url': url,
            'cid': key
        }
        urls.append(data)
    arg[0] = True
    time.sleep(0.5)
    del tmp
    del arg
    vid_quality_list : list = list()
    for item in urls:
        for i in item['url']['accept_quality']:
            if not i in vid_quality_list:
                vid_quality_list.append(i)
    vid_quality_list.sort(reverse=True)
    tmp = str()
    for i in range(len(vid_quality_list)):
        tmp += str(vid_quality_list[i])
        if i + 1 != len(vid_quality_list):
            tmp += ', '

    while True:
        try:
            vid_quality = await window_config_q(tmp)
            vid_quality = vid_quality.replace(' ', '')
            vid_quality = int(vid_quality)
            if vid_quality in vid_quality_list:
                vid_quality = int(vid_quality)
                break
            raise
        except:
            await window_warn('请输入正确的值...')
    video_codec = getUserData('video_codec')
    if video_codec is None:
        video_codec = 7
    arg = list()
    arg.append(False)
    tmp = window_downloas(arg)
    tmp.start()
    time.sleep(0.5)
    # 0: isRun, 1: t0, 2: t1, 3: t2, 4: t3, 5: bar
    if not os.path.exists('./{}'.format(removeSpecialCharacter(vid_info['title']))):
        os.mkdir('./{}'.format(removeSpecialCharacter(vid_info['title'])))
    os.chdir('./{}'.format(removeSpecialCharacter(vid_info['title'])))
    for item in urls:
        name = removeSpecialCharacter(item['name'])
        arg[1].set('正在下载 {}'.format(name))
        retry = 0
        while True:
            try:
                arg[4].set(0.0)
                arg[2].set('下载视频流')
                arg[5]['mode'] = 'determinate'
                await downloadVideo(item['url'], vid_quality, video_codec, arg, name)
                break
            except:
                retry += 1
                arg[2].set('下载失败，正在清理...')
                try:
                    os.remove('{}_temp.mp4'.format(name))
                except:
                    pass
                if retry >= 5:
                    del retry
                    raise ErrorCountsTooMuch('下载失败次数过多，请检查网络环境...')
                time.sleep(0.5)
                arg[2].set('重试...')
                time.sleep(1)
        retry = 0
        while True:
            try:
                arg[4].set(0.0)
                arg[2].set('下载音频流')
                arg[5]['mode'] = 'determinate'
                await downloadAudio(item['url'], 0, arg, name)
                break
            except:
                retry += 1
                arg[2].set('下载失败，正在清理...')
                try:
                    os.remove('{}_temp.m4a'.format(name))
                except:
                    pass
                if retry >= 5:
                    del retry
                    raise ErrorCountsTooMuch('下载失败次数过多，请检查网络环境...')
                time.sleep(0.5)
                arg[2].set('重试...')
                time.sleep(1)
        arg[2].set('开始合并')
        arg[3].set('ffmpeg')
        arg[5]['mode'] = 'indeterminate'
        arg[5].start(1)
        if os.path.exists('{}.mp4'.format(name)):
            os.remove('{}.mp4'.format(name))
        DEV_NULL = open(os.devnull, 'w')
        subprocess.run((os.path.join(programPath, 'ffmpeg/ffmpeg'),
                        '-i', '{}_temp.mp4'.format(name),
                        '-i', '{}_temp.m4a'.format(name),
                        '-vcodec', 'copy',
                        '-acodec', 'copy',
                        '{}.mp4'.format(name)),
                       stdout=DEV_NULL, stderr=subprocess.STDOUT)
        DEV_NULL.close()
        del DEV_NULL
        arg[2].set('合并完成')
        os.remove('{}_temp.mp4'.format(name))
        if isReserveAudio:
            if os.path.exists('{}.m4a'.format(name)):
                os.remove('{}.m4a'.format(name))
            os.rename('{}_temp.m4a'.format(name), '{}.m4a'.format(name))
        else:
            os.remove('{}_temp.m4a'.format(name))
        dodanmaku = getUserData('saveDanmaku')
        if dodanmaku:
            try:
                arg[2].set('下载弹幕')
                arg[3].set('正在获取弹幕...')
                dan = bili_api.danmaku.get_danmaku_xml(item['cid'])
                time.sleep(0.2)
                arg[3].set('正在解析弹幕...')
                dan = xml2ass.convertMain(dan, 852, 480, text_opacity=0.6)
                time.sleep(0.25)
                with open('{}.ass'.format(name), 'w', encoding='utf_8') as assf:
                    assf.write(dan)
                arg[3].set('弹幕下载完成...')
            except:
                arg[3].set('弹幕下载失败...')
        arg[1].set('下载完成 {}'.format(name))
        time.sleep(0.5)
        arg[5].stop()
    arg[0] = True
    time.sleep(0.5)
    del arg
    del tmp
    await window_finish(os.getcwd())
    return


async def bangumiDown(vid_id: str, passport: BiliPassport = None):
    global programPath
    isReserveAudio: Union[None, bool] = getUserData('reserveAudio')
    if isReserveAudio is None:
        isReserveAudio = False
    if vid_id[:2].lower() == 'md':
        vid_ID_type = 'md'
    else:
        vid_ID_type = 'ep'
    vid_ID = int(vid_id[2:])
    if vid_ID_type == 'md':
        vid_info = bili_api.bangumi.get_bangumi_detailed_info(media_id=vid_ID)
    else:
        vid_info = bili_api.bangumi.get_bangumi_detailed_info(ep_id=vid_ID)
    while True:
        tmp = await window_confirm(
            f'请确认番剧:\n\n下载位置: '
            f'{getUserData("downloadPath")}\n'
            f'标题: {vid_info["info"]["media"]["title"]}\n'
            f'评分: {vid_info["info"]["media"]["rating"]["score"]}\n',
            vid_info['info']['media']['cover']
        )
        if tmp:
            break
        else:
            await window_warn('退出...', playSound=False, level='信息')
            return
    vid_list = vid_info['data']
    vid_episodes : list = list()
    for i in vid_list['episodes']:
        tmp = {'aid': i['aid'],
               'cid': i['cid'],
               'name': removeSpecialCharacter(vid_info['info']['media']['title']),
               'title': removeSpecialCharacter(i['title']),
               'long_title': removeSpecialCharacter(i['long_title'])
               }
        vid_episodes.append(tmp)
    vid_episodes_count : int = len(vid_episodes)
    while True:
        vid_chose : str = await window_config_p(vid_episodes_count)
        vid_chose = vid_chose.replace(' ', '')
        try:
            vid_chose_a = vid_chose.split(',')
            vid_chose_b : list = []
            for i in vid_chose_a:
                vid_chose_b.append(i.split('-'))
            vid_chose_c : list = list()
            for i in vid_chose_b:
                if int(i[0]) > int(i[1]):
                    raise
                if int(i[1]) > vid_episodes_count:
                    raise
                tmp = list(range(int(i[0]) - 1, int(i[1])))
                for j in tmp:
                    vid_chose_c.append(vid_episodes[j])
            break
        except:
            await window_warn('请输入正确的值...')
    arg = list()
    arg.append(False)
    tmp = window_geturl(arg)
    tmp.start()
    time.sleep(0.5)
    if not os.path.exists('./{}'.format(removeSpecialCharacter(vid_info['info']['media']['title']))):
        os.mkdir('./{}'.format(removeSpecialCharacter(vid_info['info']['media']['title'])))
    os.chdir('./{}'.format(removeSpecialCharacter(vid_info['info']['media']['title'])))
    for i in vid_chose_c:
        arg[1].set(f'正在获取 {i["cid"]} 的链接...')
        errtime = 0
        errinfo = None
        while True:
            try:
                if errtime > 5:
                    await window_warn("获取视频链接错误: {}".format(errinfo), level='错误')
                    return
                i['url'] = bili_api.video.get_video_url(avid=i['aid'], cid=i['cid'], passport=passport)
                break
            except:
                errtime += 1
                errinfo = sys.exc_info()
                time.sleep(0.8)
        del errtime, errinfo
    arg[0] = True
    time.sleep(0.5)
    del tmp
    del arg
    vid_quality_list : list = list()
    for item in vid_chose_c:
        for i in item['url']['accept_quality']:
            if not i in vid_quality_list:
                vid_quality_list.append(i)
    vid_quality_list.sort(reverse=True)
    tmp = str()
    for i in range(len(vid_quality_list)):
        tmp += str(vid_quality_list[i])
        if i + 1 != len(vid_quality_list):
            tmp += ', '
    while True:
        try:
            vid_quality = await window_config_q(tmp)
            vid_quality = vid_quality.replace(' ', '')
            vid_quality = int(vid_quality)
            if vid_quality in vid_quality_list:
                vid_quality = int(vid_quality)
                break
            raise
        except:
            await window_warn('请输入正确的值...')
    video_codec = getUserData('video_codec')
    if video_codec is None:
        video_codec = 7
    # 0: isRun, 1: t0, 2: t1, 3: t2, 4: t3, 5: bar
    arg : list = list()
    arg.append(False)
    tmp = window_downloas(arg)
    tmp.start()
    time.sleep(0.5)
    for i in vid_chose_c:
        name = removeSpecialCharacter(f'{i["name"]}_第{i["title"]}话_{i["long_title"]}')
        arg[1].set(f'正在下载 {name}')
        retry = 0
        while True:
            try:
                arg[4].set(0.0)
                arg[2].set('下载视频流')
                arg[5]['mode'] = 'determinate'
                await downloadVideo(i['url'], vid_quality, video_codec, arg, name)
                break
            except:
                retry += 1
                arg[2].set('下载失败，正在清理...')
                try:
                    os.remove('{}_temp.mp4'.format(name))
                except:
                    pass
                if retry >= 5:
                    del retry
                    raise ErrorCountsTooMuch('下载失败次数过多，请检查网络环境...')
                time.sleep(0.5)
                arg[2].set('重试...')
                time.sleep(1)
        retry = 0
        while True:
            try:
                arg[4].set(0.0)
                arg[2].set('下载音频流')
                arg[5]['mode'] = 'determinate'
                await downloadAudio(i['url'], 0, arg, name)
                break
            except:
                retry += 1
                arg[2].set('下载失败，正在清理...')
                try:
                    os.remove('{}_temp.m4a'.format(name))
                except:
                    pass
                if retry >= 5:
                    del retry
                    raise ErrorCountsTooMuch('下载失败次数过多，请检查网络环境...')
                time.sleep(0.5)
                arg[2].set('重试...')
                time.sleep(1)
        arg[2].set('开始合并')
        arg[3].set('ffmpeg')
        arg[5]['mode'] = 'indeterminate'
        arg[5].start(1)
        if os.path.exists('{}.mp4'.format(name)):
            os.remove('{}.mp4'.format(name))
        DEV_NULL = open(os.devnull, 'w')
        subprocess.run((os.path.join(programPath, 'ffmpeg/ffmpeg'),
                        '-i', '{}_temp.mp4'.format(name),
                        '-i', '{}_temp.m4a'.format(name),
                        '-vcodec', 'copy',
                        '-acodec', 'copy',
                        '{}.mp4'.format(name)),
                       stdout=DEV_NULL, stderr=subprocess.STDOUT)
        DEV_NULL.close()
        del DEV_NULL
        arg[2].set('合并完成')
        os.remove('{}_temp.mp4'.format(name))
        if isReserveAudio:
            if os.path.exists('{}.m4a'.format(name)):
                os.remove('{}.m4a'.format(name))
            os.rename('{}_temp.m4a'.format(name), '{}.m4a'.format(name))
        else:
            os.remove('{}_temp.m4a'.format(name))
        dodanmaku = getUserData('saveDanmaku')
        if dodanmaku:
            arg[2].set('下载弹幕')
            arg[3].set('正在获取弹幕...')
            dan = bili_api.danmaku.get_danmaku_xml(i['cid'])
            time.sleep(0.2)
            arg[3].set('正在解析弹幕...')
            dan = xml2ass.convertMain(dan, 852, 480, text_opacity=0.6)
            time.sleep(0.25)
            with open('{}.ass'.format(name), 'w', encoding='utf_8') as assf:
                assf.write(dan)
            arg[3].set('弹幕下载完成...')
        arg[1].set('下载完成 {}'.format(name))
        time.sleep(0.5)
        arg[5].stop()
    arg[0] = True
    time.sleep(0.5)
    del arg
    del tmp
    await window_finish(os.getcwd())
    return


async def start_download_video(id_get : str):
    passportRaw = getUserData('passport')
    passport = None
    if passportRaw is not None:
        passportRaw = passportRaw['data']
        passportRaw.pop('Expires')
        passport = BiliPassport(passportRaw)
    mode = 'none'
    id_out = ''
    available: tuple = ('bv', 'av', 'md', 'ep')
    matchMode = matchFomat.matchAll(id_get)
    if matchMode is None:
        await window_warn('请输入正确的值...')
        return False
    if matchMode == 'MD' or matchMode == 'EP':
        mode = 'bangumi'
        if matchMode == 'MD':
            id_out = matchFomat.getMdid(id_get)
        else:
            id_out = matchFomat.getEpid(id_get)
    elif matchMode == 'BV' or matchMode == 'AV':
        mode = 'video'
        if matchMode == 'BV':
            id_out = matchFomat.getBvid(id_get)
        else:
            id_out = matchFomat.getAvid(id_get)
    else:
        await window_warn('请输入正确的值...')
        return False
    if mode == 'bangumi':
        await bangumiDown(id_out, passport)
    elif mode == 'video':
        await videoDown(id_out, passport)
    return True


async def start_settings():
    global programPath
    dafult = getUserData('passport')
    isReserveAudio: Union[None, bool] = getUserData('reserveAudio')
    isSaveDanmaku: Union[None, bool] = getUserData('saveDanmaku')
    getVCodec: Union[None, int] = getUserData('video_codec')
    if dafult is not None:
        dafult = dafult['ts'] + int(dafult['data']['Expires']) - time.time()
    if isReserveAudio is None:
        isReserveAudio = False
    if isSaveDanmaku is None:
        isSaveDanmaku = False
    if getVCodec is None:
        getVCodec = 7
    config = Window_settings_config(getUserData('downloadPath'), dafult, isReserveAudio, isSaveDanmaku, getVCodec)
    tmp = await window_settings(config)
    if tmp is None:
        return False
    if tmp[0] == 0:
        if os.path.exists(tmp[1]):
            setUserData('downloadPath', tmp[1])
            await window_warn('下载目录更改成功!', level='成功')
            os.chdir(tmp[1])
            return False
        elif tmp[1] == '':
            return False
        else:
            await window_warn('目录无法设置', level='错误')
            return False
    elif tmp[0] == 1:
        passport_new = user_login()
        if passport_new is not None:
            setUserData('passport', passport_new)
            await window_warn('设置成功，请重新启动程序...', playSound=False, level='信息')
            return True
        else:
            await window_warn('登录失败...', playSound=False, level='信息')
            return False
    elif tmp[0] == 2:
        reSetUserData()
        await window_warn('设置重置成功，请重新启动程序...', playSound=False, level='信息')
        return True
    elif tmp[0] == 3:
        setUserData('reserveAudio', tmp[1])
        setUserData('saveDanmaku', tmp[2])
        setUserData('video_codec', tmp[3])
        return False


async def Main():
    global ver
    global PID
    showUpdateInfo(ver)
    tmp = list()
    tmp.append(False)
    update_window = window_checkUpdate(tmp)
    update_window.start()
    try:
        ver_get = await checkUpdate()
    except:
        await window_warn('网络错误...(如果你的网络正常，可能是作者的服务器挂了...)', level='错误')
        ver_get = ver
    tmp[0] = True
    time.sleep(0.2)
    try:
        if not ifuptodate(ver, ver_get):
            await window_showupdate()
            await window_showupdate_detal(getUpdateInfo())
            await getUpdate(ver_get)
    except ErrorDownloadHash as e:
        await window_warn('更新失败: {}'.format(str(e)), level='错误')
        return 1
    except:
        await window_warn('更新失败: {} {}'.format(sys.exc_info()[0], sys.exc_info()[1]), level='错误')
        return 1
    del update_window, tmp


    passCheck = getUserData('passport')
    if passCheck is not None:
        if passCheck['ts'] + int(passCheck['data']['Expires']) < time.time():
            await window_warn('账号登录信息已过期，请尽快重新登录...')

    while True:
        get = await window_ask()
        if get[0] == 0:
            try:
                tmp = await start_download_video(get[1])
                if tmp:
                    break
            except exceptions.BiliVideoIdException as e:
                await window_warn('输入错误: {}'.format(e), level='错误')
            except exceptions.NetWorkException as e:
                await window_warn('网络错误: {}'.format(e), level='错误')
            except ErrorCountsTooMuch as e:
                await window_warn(str(e), level='错误')
                break
            except ErrorCredential as e:
                await window_warn(str(e), level='错误')
                break
            except:
                await window_warn(f'错误: {sys.exc_info()[0]}, {sys.exc_info()[1]}, {sys.exc_info()[2]}\n{traceback.format_exc()}', level='错误')
                break
        elif get[0] == 1:
            tmp = await start_settings()
            if tmp:
                break


if __name__ == '__main__':
    ver = '0.13.0'
    if not os.path.exists('./Download'):
        os.mkdir('./Download')
    programPath = os.getcwd()
    path = getUserData('downloadPath')
    if path is None:
        os.chdir('./Download')
    else:
        if os.path.exists(path):
            os.chdir(path)
        else:
            removeUserData('downloadPath')
            os.chdir('./Download')
    del path
    PID = os.getpid()
    window_setVar(PID, programPath)
    # debug
    # window.set_icon(None)
    asyncio.get_event_loop().run_until_complete(Main())
    os.kill(PID, 15)
