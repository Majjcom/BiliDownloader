# Copyright © 2022 BiliDownloader
# Made by Majjcom
from bili_api.utils import BiliPassport, cookieTools
from bili_api import exceptions
from threading import Event
from bdnet import client
from window import *
import subprocess
import threadDown
import bili_api
import aiohttp
import asyncio
import hashlib
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


async def downloadVideo(Url : dict, qid : int, v, name : str = 'video'):
    global mainprocess, programPath
    async with aiohttp.ClientSession() as sess:
        video_url = Url['dash']['video'][0]['baseUrl']
        for i in Url['dash']['video']:
            if i['codecid'] == 7:
                if i['id'] == qid:
                    video_url = i['baseUrl']
        HEADERS = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bilibili.com/'
        }
        await threadDown.download_with_threads(video_url, v, '{}_temp.mp4'.format(name), headers=HEADERS, piece_per_size=(64 * 1024 ** 2))


async def downloadAudio(Url : dict, id : int, v, name : str = 'audio'):
    global mainprocess
    async with aiohttp.ClientSession() as sess:
        audio_url = Url['dash']['audio'][0]['baseUrl']
        HEADERS = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bilibili.com/'
        }
        await threadDown.download_with_threads(audio_url, v, '{}_temp.m4a'.format(name), headers=HEADERS, piece_per_size=(64 * 1024 ** 2))


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
    return (get['content']['url'], get['content']['hash'])


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
    if not os.path.exists(os.path.join(programPath, 'data')):
        os.mkdir(os.path.join(programPath, 'data'))
    if not os.path.exists(os.path.join(programPath, 'data/userdata.json')):
        with open(os.path.join(programPath, 'data/userdata.json'), 'w') as f:
            meta = {
                'version': ver,
                'isnew': False if reset else True,
                'userinfo': dict()
            }
            json.dump(meta, f, sort_keys=True, indent=4)


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
        json.dump(userdata, f, sort_keys=True, indent=4)
    return True


def reSetUserData():
    global programPath
    setupUserData()
    os.remove(os.path.join(programPath, 'data/userdata.json'))
    setupUserData(reset=True)


def showUpdateInfo(ver : str):
    global programPath
    try:
        new_user = getUserData('isnew')
        ver_get = getUserData('version')
        if not ifuptodate(ver_get, ver):
            new_user = True
            setUserData('version', ver)
        if new_user:
            setUserData('isnew', False)
            os.startfile(os.path.realpath(os.path.join(programPath, 'src/CHANGELOG.txt')))
    except:
        raise
    finally:
        del new_user


def user_login():
    try:
        login_info = bili_api.user.get_login_url()
        subprocess.run((
            os.path.join(programPath, 'bin/qrMaker.exe'),
            '--in={}'.format(login_info['data']['url']),
            '--out={}'.format(os.path.join(programPath, 'data/qrcode.png'))
        ))
        e0, e1, e2 = Event(), Event(), Event()
        Window_login(os.path.join(programPath, 'data/qrcode.png'), e0, e1, e2).start()
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
                elif e2.is_set():
                    break
                else:
                    if tmp['data'] < -4:
                        e0.set()
                    elif 0 > tmp['data'] > -3:
                        e2.set()
                        break
                time.sleep(0.5)
        if os.path.exists(os.path.join(programPath, 'data/qrcode.png')):
            os.remove(os.path.join(programPath, 'data/qrcode.png'))
        return ret
    except:
        return None


async def videoDown(vid_id : str, passport: BiliPassport = None):
    global programPath
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
    if vid_id_isBV:
        vid_info = bili_api.video.get_video_info(bvid=vid_ID)
    else:
        vid_info = bili_api.video.get_video_info(aid=vid_ID)
    vid_pages = vid_info['pages']
    tmp = await window_confirm('请确认视频:\n\n下载位置: {}\n标题: {}\nUP主: {}'.format(getUserData('downloadPath'), vid_info['title'], vid_info['owner']['name']))
    if not tmp:
        await window_warn('退出...', playSound=False, level='信息')
        return
    vid_pages_count : int = len(vid_pages)
    while True:
        vid_chose : str = await window_config_p('分P列表中共有{}个视频'.format(vid_pages_count))
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
                errinfo = sys.exc_info()
                time.sleep(0.8)
        del errtime, errinfo
        data = {
            'name': '{}_{}_{}'.format(vid_info['title'].replace(' ', '_'), vid_chose_c[key]['page'], vid_chose_c[key]['part'].replace(' ', '_')),
            'url': url
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
    arg = list()
    arg.append(False)
    tmp = window_downloas(arg)
    tmp.start()
    time.sleep(0.5)
    # 0: isRun, 1: t0, 2: t1, 3: t2, 4: t3, 5: bar
    for item in urls:
        name = item['name'].replace('/', '').replace('\\', '')
        arg[1].set('开始下载 {}'.format(name))
        retry = 0
        while True:
            try:
                arg[4].set(0.0)
                arg[2].set('下载视频流')
                arg[5]['mode'] = 'determinate'
                await downloadVideo(item['url'], vid_quality, arg, name)
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
        os.remove('{}_temp.m4a'.format(name))
        arg[1].set('{} 下载完成'.format(name))
        time.sleep(0.5)
        arg[5].stop()
    arg[0] = True
    time.sleep(0.5)
    del arg
    del tmp
    await window_finish(os.getcwd())
    return


async def bangumiDown(vid_id : str, passport: BiliPassport = None):
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
        tmp = await window_confirm(f'请确认番剧:\n\n下载位置: {getUserData("downloadPath")}\n标题: {vid_info["info"]["media"]["title"]}\n评分: {vid_info["info"]["media"]["rating"]["score"]}')
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
               'name': vid_info['info']['media']['title'].replace(' ', '_'),
               'title': i['title'],
               'long_title': i['long_title'].replace(' ', '_')
               }
        vid_episodes.append(tmp)
    vid_episodes_count : int = len(vid_episodes)
    while True:
        vid_chose : str = await window_config_p('分P列表中共有{}个视频'.format(vid_episodes_count))
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
    # 0: isRun, 1: t0, 2: t1, 3: t2, 4: t3, 5: bar
    arg : list = list()
    arg.append(False)
    tmp = window_downloas(arg)
    tmp.start()
    time.sleep(0.5)
    for i in vid_chose_c:
        name = f'{i["name"]}_第{i["title"]}话_{i["long_title"]}'.replace('/', '').replace('\\', '')
        arg[1].set(f'开始下载 {name}')
        retry = 0
        while True:
            try:
                arg[4].set(0.0)
                arg[2].set('下载视频流')
                arg[5]['mode'] = 'determinate'
                await downloadVideo(i['url'], vid_quality, arg, name)
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
        os.remove('{}_temp.m4a'.format(name))
        arg[1].set('{} 下载完成'.format(name))
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
    available: tuple = ('bv', 'av', 'md', 'ep')
    if id_get[:2].lower() in available:
        if id_get[:2].lower() == 'md' or id_get[:2].lower() == 'ep':
            mode = 'bangumi'
        elif id_get[:2].lower() == 'bv' or id_get[:2].lower() == 'av':
            mode = 'video'
    else:
        await window_warn('请输入正确的值...')
        return False
    if mode == 'bangumi':
        await bangumiDown(id_get, passport)
    elif mode == 'video':
        await videoDown(id_get, passport)
    return True


async def start_settings():
    global programPath
    dafult = getUserData('passport')
    tmp = await window_settings(getUserData('downloadPath'), True if dafult else False)
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
                del tmp
            except exceptions.BiliVideoIdException as e:
                await window_warn('输入错误: {}'.format(e), level='错误')
            except exceptions.NetWorkException as message:
                await window_warn('网络错误: {}'.format(message), level='错误')
            except ErrorCountsTooMuch as e:
                await window_warn(str(e), level='错误')
                break
            except ErrorCredential as e:
                await window_warn(str(e), level='错误')
                break
            except:
                await window_warn(f'错误: {sys.exc_info()[0]}, {sys.exc_info()[1]}, {sys.exc_info()[2]}', level='错误')
                break
        elif get[0] == 1:
            tmp = await start_settings()
            if tmp:
                break
            del tmp


if __name__ == '__main__':
    ver = '0.11.0'
    if not os.path.exists('./Download'):
        os.mkdir('./Download')
    programPath = os.getcwd()
    path = getUserData('downloadPath')
    if path is None:
        os.chdir('./Download')
    else:
        os.chdir(path)
    del path
    PID = os.getpid()
    window_setVar(PID, programPath)
    asyncio.get_event_loop().run_until_complete(Main())
    os.kill(PID, 15)
