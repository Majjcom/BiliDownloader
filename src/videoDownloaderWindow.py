# Copyright © 2022 BiliDownloader
# Made by Majjcom
from bilibili_api import Credential, video, bangumi, exceptions
from threadDown.utils import sizefstr
from bdnet import client
from window import *
import subprocess
import threadDown
import aiohttp
import asyncio
import hashlib
import json
import time
import sys
import os

class ErrorCountsTooMuch(Exception):
    def __init__(self, info : str = None):
        Exception.__init__(self);
        self.info : str = info;
    def __str__(self):
        return self.info;

class ErrorDownloadHash(Exception):
    def __init__(self, info : str = None):
        Exception.__init__(self);
        self.info = info;
    def __str__(self):
        return self.info;


class ErrorCredential(Exception):
    def __init__(self, info : str = None):
        Exception.__init__(self);
        self.info = info;
    def __str__(self):
        return self.info;


async def downloadVideo(Url : dict, qid : int, v, name : str = 'video'):
    global mainprocess, programPath;
    async with aiohttp.ClientSession() as sess:
        video_url = Url['dash']['video'][0]['baseUrl'];
        for i in Url['dash']['video']:
            if i['codecid'] == 7:
                if i['id'] == qid:
                    video_url = i['baseUrl'];
        HEADERS = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bilibili.com/'
        };
        await threadDown.download_with_threads(video_url, v, '{}_temp.mp4'.format(name), headers=HEADERS, piece_per_size=(128 * 1024 ** 2));


async def downloadAudio(Url : dict, id : int, v, name : str = 'audio'):
    global mainprocess;
    async with aiohttp.ClientSession() as sess:
        audio_url = Url['dash']['audio'][0]['baseUrl'];
        HEADERS = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bilibili.com/'
        };
        await threadDown.download_with_threads(audio_url, v, '{}_temp.m4a'.format(name), headers=HEADERS, piece_per_size=(64 * 1024 ** 2))


async def checkUpdate():
    global ver;
    c = client.Connection('www.majjcom.site', 11288);
    c.sendMsg({'action': 'version', 'after': True, 'bVersion': ver});
    get = c.recvMsg();
    c.close();
    return get['content'];


def ifuptodate(now: str, get: str) -> bool:
    a_s = now.split('.');
    b_s = get.split('.');
    for i in range(3):
        if int(a_s[i]) > int(b_s[i]):
            return True;
        elif int(a_s[i]) == int(b_s[i]):
            continue;
        else:
            return False;
    return True;


async def getUpdate(ver):
    name = f'BiliDownloader{ver}_Installer.exe';
    info = getUpdateUrl();
    # url = f'http://d.majjcom.site:1288/file/{name}';
    url = info[0];
    realHash = info[1]
    arg : list = list();
    arg.append(False);
    win = window_updating(arg);
    win.start();
    time.sleep(0.5);
    if not os.path.exists(name):
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                length = int(resp.headers.get('content-length'));
                with open(name, 'w+b') as f:
                    process = 0;
                    count = 0;
                    while True:
                        chunk = await resp.content.read(1024);
                        process += len(chunk);
                        count += 1;
                        if not chunk:
                            arg[1].set(100.0);
                            f.close();
                            await sess.close();
                            break;
                        if count % 512 == 0:
                            arg[1].set(round(process / length * 100, 2));
                        f.write(chunk);
    fileHash = getFileHash(name);
    if fileHash.lower() != realHash.lower():
        if os.path.exists(name):
            os.remove(name);
        raise ErrorDownloadHash('文件下载不完整...');
    arg[0] = True;
    time.sleep(0.3);
    os.system(name);
    time.sleep(0.2);
    global PID;
    os.kill(PID, 9);


def getUpdateUrl():
    global ver;
    s = client.Connection('www.majjcom.site', 11288);
    s.sendMsg({'action': 'updateUrl', 'bVersion': ver});
    get = s.recvMsg();
    return (get['content']['url'], get['content']['hash']);


def getFileHash(name):
    f = open(name, 'rb');
    Md5_buffer = hashlib.md5();
    for buff in iter(lambda: f.read(1024), b''):
        Md5_buffer.update(buff);
    f.close();
    return Md5_buffer.hexdigest();


def setupUserData(reset: bool = False) -> None:
    global programPath;
    if not os.path.exists(os.path.join(programPath, 'data')):
        os.mkdir(os.path.join(programPath, 'data'));
    if not os.path.exists(os.path.join(programPath, 'data/userdata.json')):
        with open(os.path.join(programPath, 'data/userdata.json'), 'w') as f:
            meta = {
                'version': ver,
                'isnew': False if reset else True,
                'userinfo': dict()
            };
            json.dump(meta, f);


def getUserData(key : str):
    global programPath;
    keywd = ('version', 'isnew');
    setupUserData();
    with open(os.path.join(programPath, 'data/userdata.json'), 'r') as f:
        userdata = json.load(f);
    if key in keywd:
        return userdata[key];
    if key in userdata['userinfo']:
        return userdata['userinfo'][key];
    return None;


def setUserData(key : str, value : {dict, list, int, float, str}) -> bool:
    global programPath;
    keywd = ('version', 'isnew');
    setupUserData();
    with open(os.path.join(programPath, 'data/userdata.json'), 'r') as f:
        userdata = json.load(f);
    if key in keywd:
        userdata[key] = value;
    else:
        userdata['userinfo'][key] = value;
    with open(os.path.join(programPath, 'data/userdata.json'), 'w') as f:
        json.dump(userdata, f);
    return True;


def reSetUserData():
    global programPath;
    setupUserData();
    os.remove(os.path.join(programPath, 'data/userdata.json'))
    setupUserData(reset=True)


def showUpdateInfo(ver : str):
    global programPath;
    try:
        new_user = getUserData('isnew');
        ver_get = getUserData('version');
        if not ifuptodate(ver_get, ver):
            new_user = True;
            setUserData('version', ver);
        if new_user:
            setUserData('isnew', False);
            os.startfile(os.path.realpath(os.path.join(programPath, 'src/CHANGELOG.txt')));
    except:
        raise;
        pass;
    finally:
        del new_user;


async def videoDown(vid_id : str, credential = None):
    global programPath;
    if credential is None:
        haveCred = False;
    else:
        haveCred = True;
    vid_id_isBV : bool = None;
    if len(vid_id) <= 2:
        pass;
    elif vid_id[:2].lower() == 'bv':
        vid_id_isBV = True;
    elif vid_id[:2].lower() == 'av':
        vid_id_isBV = False;
    if vid_id_isBV:
        vid_ID = vid_id;
    else:
        vid_ID = int(vid_id[2:]);
    v : video.Video() = None;
    if vid_id_isBV:
        v = video.Video(bvid=vid_ID, credential=credential if haveCred else None)
    else:
        v = video.Video(aid=vid_ID, credential=credential if haveCred else None)
    vid_info = await v.get_info();
    vid_pages = await v.get_pages();
    del v;
    while True:
        tmp = await window_confirm('请确认视频:\n\n下载位置: {}\n标题: {}\nUP主: {}'.format(getUserData('downloadPath'), vid_info['title'], vid_info['owner']['name']));
        if tmp:
            break;
        else:
            await window_warn('退出...', playSound=False);
            return;
        del tmp;
    vid_pages_count : int = len(vid_pages);
    while True:
        vid_chose : str = await window_config_p('分P列表中共有{}个视频'.format(vid_pages_count));
        vid_chose = vid_chose.replace(' ', '');
        try:
            vid_chose_a = vid_chose.split(',');
            vid_chose_b : list = [];
            for i in vid_chose_a:
                vid_chose_b.append(i.split('-'));
            vid_chose_c : dict = {};
            for i in vid_chose_b:
                if int(i[0]) > int(i[1]):
                    raise;
                if int(i[1]) > vid_pages_count:
                    raise;
                tmp = list(range(int(i[0]) - 1, int(i[1])));
                for j in tmp:
                    vid_chose_c[vid_pages[j]['cid']] = {'page': vid_pages[j]['page'], 'part': vid_pages[j]['part']};
            break;
        except:
            await window_warn('请输入正确的值...');
    urls : list = list();
    arg = list();
    arg.append(False);
    tmp = window_geturl(arg);
    tmp.start();
    time.sleep(0.5);
    for key in vid_chose_c:
        arg[1].set('正在获取 {} 的链接'.format(key));
        if vid_id_isBV:
            v = video.Video(bvid=vid_ID, credential=credential if haveCred else None)
        else:
            v = video.Video(aid=vid_ID, credential=credential if haveCred else None)
        errtime = 0;
        errinfo = None;
        while True:
            try:
                if errtime > 5:
                    await window_warn("获取视频链接错误: {}".format(errinfo));
                    return;
                tmp_info = await v.get_info()
                if tmp_info['copyright'] == 2 and credential is None:
                    await window_warn('您正尝试下载会员资源，但您未设置通行证，请前往设置中设置...');
                    return;
                url = await v.get_download_url(cid=key);
                break;
            except:
                errtime += 1;
                errinfo = sys.exc_info();
                time.sleep(0.8);
        del v, errtime, errinfo;
        data = {
            'name': '{}_{}_{}'.format(vid_info['title'].replace(' ', '_'), vid_chose_c[key]['page'], vid_chose_c[key]['part'].replace(' ', '_')),
            'url': url
        }
        urls.append(data)
    arg[0] = True;
    time.sleep(0.5);
    del tmp;
    del arg;
    vid_quality_list : list = list()
    for item in urls:
        for i in item['url']['accept_quality']:
            if not i in vid_quality_list:
                vid_quality_list.append(i)
    vid_quality_list.sort(reverse=True)
    tmp = str();
    for i in range(len(vid_quality_list)):
        tmp += str(vid_quality_list[i]);
        if i + 1 != len(vid_quality_list):
            tmp += ', ';

    while True:
        try:
            vid_quality = await window_config_q(tmp);
            vid_quality = vid_quality.replace(' ', '');
            vid_quality = int(vid_quality);
            if vid_quality in vid_quality_list:
                vid_quality = int(vid_quality);
                break;
            raise;
        except:
            await window_warn('请输入正确的值...');
    arg = list();
    arg.append(False);
    tmp = window_downloas(arg);
    tmp.start();
    time.sleep(0.5);
    # 0: isRun, 1: t0, 2: t1, 3: t2, 4: t3, 5: bar
    for item in urls:
        name = item['name']
        arg[1].set('开始下载 {}'.format(name));
        retry = 0;
        while True:
            try:
                arg[4].set(0.0);
                arg[2].set('下载视频流');
                arg[5]['mode'] = 'determinate';
                await downloadVideo(item['url'], vid_quality, arg, name);
                break;
            except:
                retry += 1;
                arg[2].set('下载失败，正在清理...');
                try:
                    os.remove('{}_temp.mp4'.format(name));
                except:
                    pass;
                if retry >= 5:
                    del retry;
                    raise ErrorCountsTooMuch('下载失败次数过多，请检查网络环境...');
                time.sleep(0.5);
                arg[2].set('重试...');
                time.sleep(1);
        retry = 0;
        while True:
            try:
                arg[4].set(0.0);
                arg[2].set('下载音频流');
                arg[5]['mode'] = 'determinate';
                await downloadAudio(item['url'], 0, arg, name);
                break;
            except:
                retry += 1;
                arg[2].set('下载失败，正在清理...');
                try:
                    os.remove('{}_temp.m4a'.format(name));
                except:
                    pass;
                if retry >= 5:
                    del retry;
                    raise ErrorCountsTooMuch('下载失败次数过多，请检查网络环境...');
                time.sleep(0.5);
                arg[2].set('重试...');
                time.sleep(1);
        arg[2].set('开始合并');
        arg[3].set('ffmpeg');
        arg[5]['mode'] = 'indeterminate';
        arg[5].start(1);
        if os.path.exists('{}.mp4'.format(name)):
            os.remove('{}.mp4'.format(name));
        DEV_NULL = open(os.devnull, 'w');
        subprocess.run((os.path.join(programPath, 'ffmpeg/ffmpeg'),
                        '-i', '{}_temp.mp4'.format(name),
                        '-i', '{}_temp.m4a'.format(name),
                        '-vcodec', 'copy',
                        '-acodec', 'copy',
                        '{}.mp4'.format(name)),
                       stdout=DEV_NULL, stderr=subprocess.STDOUT);
        DEV_NULL.close();
        del DEV_NULL;
        arg[2].set('合并完成');
        os.remove('{}_temp.mp4'.format(name));
        os.remove('{}_temp.m4a'.format(name));
        arg[1].set('{} 下载完成'.format(name));
        time.sleep(0.5);
        arg[5].stop();
    arg[0] = True;
    time.sleep(0.5);
    del arg;
    del tmp;
    await window_finish(os.getcwd());
    return;


async def bangumiDown(vid_id : str, credential = None):
    if credential is None:
        haveCred = False;
    else:
        haveCred = True;
    vid_info = dict;
    if haveCred:
        vid_info = await bangumi.get_meta(int(vid_id[2:]), credential=credential);
    else:
        vid_info = await bangumi.get_meta(int(vid_id[2:]), credential=credential);
    while True:
        tmp = await window_confirm(f'请确认番剧:\n\n下载位置: {getUserData("downloadPath")}\n标题: {vid_info["media"]["title"]}\n评分: {vid_info["media"]["rating"]["score"]}');
        if tmp:
            break;
        else:
            await window_warn('退出...', playSound=False);
            return;
    vid_list : dict = None;
    if haveCred:
        vid_list = await bangumi.get_episode_list(vid_info['media']['season_id'], credential=credential);
    else:
        vid_list = await bangumi.get_episode_list(vid_info['media']['season_id']);
    vid_episodes : list = list()
    for i in vid_list['main_section']['episodes']:
        tmp = {'aid': i['aid'],
               'cid': i['cid'],
               'name': vid_info['media']['title'].replace(' ', '_'),
               'title': i['title'],
               'long_title': i['long_title'].replace(' ', '_')
               };
        vid_episodes.append(tmp);
    vid_episodes_count : int = len(vid_episodes);
    while True:
        vid_chose : str = await window_config_p('分P列表中共有{}个视频'.format(vid_episodes_count));
        vid_chose = vid_chose.replace(' ', '');
        try:
            vid_chose_a = vid_chose.split(',');
            vid_chose_b : list = [];
            for i in vid_chose_a:
                vid_chose_b.append(i.split('-'));
            vid_chose_c : list = list();
            for i in vid_chose_b:
                if int(i[0]) > int(i[1]):
                    raise;
                if int(i[1]) > vid_episodes_count:
                    raise;
                tmp = list(range(int(i[0]) - 1, int(i[1])));
                for j in tmp:
                    vid_chose_c.append(vid_episodes[j]);
            break;
        except:
            await window_warn('请输入正确的值...');
    arg = list();
    arg.append(False);
    tmp = window_geturl(arg);
    tmp.start();
    time.sleep(0.5);
    for i in vid_chose_c:
        arg[1].set(f'正在获取 {i["cid"]} 的链接...')
        if haveCred:
            v = video.Video(aid=i['aid'], credential=credential);
        else:
            v = video.Video(aid=i['aid']);
        errtime = 0;
        errinfo = None;
        while True:
            try:
                if errtime > 5:
                    await window_warn("获取视频链接错误: {}".format(errinfo));
                    return;

                tmp_info = await v.get_info()
                if tmp_info['copyright'] == 2 and credential is None:
                    await window_warn('您正尝试下载会员资源，但您未设置通行证，请前往设置中设置...');
                    return;
                i['url'] = await v.get_download_url(cid=i['cid']);
                break;
            except:
                errtime += 1;
                errinfo = sys.exc_info();
                time.sleep(0.8);
        del v, errtime, errinfo;
    arg[0] = True;
    time.sleep(0.5);
    del tmp;
    del arg;
    vid_quality_list : list = list()
    for item in vid_chose_c:
        for i in item['url']['accept_quality']:
            if not i in vid_quality_list:
                vid_quality_list.append(i)
    vid_quality_list.sort(reverse=True)
    tmp = str();
    for i in range(len(vid_quality_list)):
        tmp += str(vid_quality_list[i]);
        if i + 1 != len(vid_quality_list):
            tmp += ', ';
    while True:
        try:
            vid_quality = await window_config_q(tmp);
            vid_quality = vid_quality.replace(' ', '');
            vid_quality = int(vid_quality);
            if vid_quality in vid_quality_list:
                vid_quality = int(vid_quality);
                break;
            raise;
        except:
            await window_warn('请输入正确的值...');
    # 0: isRun, 1: t0, 2: t1, 3: t2, 4: t3, 5: bar
    arg : list = list();
    arg.append(False);
    tmp = window_downloas(arg);
    tmp.start();
    time.sleep(0.5);
    for i in vid_chose_c:
        name = f'{i["name"]}_第{i["title"]}话_{i["long_title"]}';
        arg[1].set(f'开始下载 {name}');
        retry = 0;
        while True:
            try:
                arg[4].set(0.0);
                arg[2].set('下载视频流');
                arg[5]['mode'] = 'determinate';
                await downloadVideo(i['url'], vid_quality, arg, name);
                break;
            except:
                retry += 1;
                arg[2].set('下载失败，正在清理...');
                try:
                    os.remove('{}_temp.mp4'.format(name));
                except:
                    pass;
                if retry >= 5:
                    del retry;
                    raise ErrorCountsTooMuch('下载失败次数过多，请检查网络环境...');
                time.sleep(0.5);
                arg[2].set('重试...');
                time.sleep(1);
        retry = 0;
        while True:
            try:
                arg[4].set(0.0);
                arg[2].set('下载音频流');
                arg[5]['mode'] = 'determinate';
                await downloadAudio(i['url'], 0, arg, name);
                break;
            except:
                retry += 1;
                arg[2].set('下载失败，正在清理...');
                try:
                    os.remove('{}_temp.m4a'.format(name));
                except:
                    pass;
                if retry >= 5:
                    del retry;
                    raise ErrorCountsTooMuch('下载失败次数过多，请检查网络环境...');
                time.sleep(0.5);
                arg[2].set('重试...');
                time.sleep(1);
        arg[2].set('开始合并');
        arg[3].set('ffmpeg');
        arg[5]['mode'] = 'indeterminate';
        arg[5].start(1);
        if os.path.exists('{}.mp4'.format(name)):
            os.remove('{}.mp4'.format(name));
        DEV_NULL = open(os.devnull, 'w');
        subprocess.run((os.path.join(programPath, 'ffmpeg/ffmpeg'),
                        '-i', '{}_temp.mp4'.format(name),
                        '-i', '{}_temp.m4a'.format(name),
                        '-vcodec', 'copy',
                        '-acodec', 'copy',
                        '{}.mp4'.format(name)),
                       stdout=DEV_NULL, stderr=subprocess.STDOUT);
        DEV_NULL.close();
        del DEV_NULL;
        arg[2].set('合并完成');
        os.remove('{}_temp.mp4'.format(name));
        os.remove('{}_temp.m4a'.format(name));
        arg[1].set('{} 下载完成'.format(name));
        time.sleep(0.5);
        arg[5].stop();
    arg[0] = True;
    time.sleep(0.5);
    del arg;
    del tmp;
    await window_finish(os.getcwd());
    return;


async def start_download_video(id : str):
    # Bilibili Account Credential
    try:
        cred = getUserData('credential');
        if cred is not None:
            credential = Credential(sessdata=cred['sessdata'], bili_jct=cred['bili_jct'], buvid3=cred['buvid3']);
        else:
            credential = None;
        del cred;
    except:
        raise ErrorCredential('通行证错误，请重新设置...');
    haveCred: bool = None;
    if credential:
        haveCred = True;
    else:
        haveCred = False
    mode = 'none';
    available: tuple = ('bv', 'av', 'md');
    if id[:2].lower() in available:
        if id[:2].lower() == 'md':
            mode = 'bangumi';
        elif id[:2].lower() == 'bv' or id[:2].lower() == 'av':
            mode = 'video';
    else:
        await window_warn('请输入正确的值...');
        return False;
    if mode == 'bangumi':
        if haveCred:
            await bangumiDown(id, credential);
        else:
            await bangumiDown(id);
    elif mode == 'video':
        if haveCred:
            await videoDown(id, credential);
        else:
            await videoDown(id);
    return True;


async def start_settings():
    global programPath;
    dafult = getUserData('credential');
    tmp = await window_settings(getUserData('downloadPath'), True if dafult else False);
    if tmp is None:
        return False;
    if tmp[0] == 0:
        if os.path.exists(tmp[1]):
            setUserData('downloadPath', tmp[1]);
            await window_warn('下载目录更改成功，请重新启动程序...');
            return True;
        elif tmp[1] == '':
            return False;
        else:
            await window_warn('目录无法设置');
            return False;
    elif tmp[0] == 1:
        cred_new = await window_settings_credential(dafult);
        if cred_new is None:
            return False;
        for i in cred_new:
            if cred_new[i] == '':
                await window_warn('请输入完整信息...');
                return False;
        setUserData('credential', cred_new);
        await window_warn('设置成功，请重新启动程序...', playSound=False);
        return True;
    elif tmp[0] == 2:
        reSetUserData()
        await window_warn('设置重置成功，请重新启动程序...', playSound=False);
        return True


async def Main():
    global ver;
    global PID;
    showUpdateInfo(ver);
    tmp = list();
    tmp.append(False);
    update_window = window_checkUpdate(tmp);
    update_window.start();
    try:
        ver_get = await checkUpdate();
    except:
        await window_warn('网络错误...(如果你的网络正常，可能是作者的服务器挂了...)');
        ver_get = ver;
    tmp[0] = True;
    time.sleep(0.2);
    try:
        if not ifuptodate(ver, ver_get):
            await window_showupdate();
            await getUpdate(ver_get);
    except ErrorDownloadHash as e:
        await window_warn('更新失败: {}'.format(str(e)));
        return 1;
    except:
        await window_warn('更新失败: {} {}'.format(sys.exc_info()[0], sys.exc_info()[1]));
        return 1;
    del update_window, tmp;

    while True:
        get = await window_ask();
        if get[0] == 0:
            try:
                tmp = await start_download_video(get[1]);
                if tmp:
                    break;
                del tmp;
            except exceptions.ResponseCodeException:
                await window_warn('404，未找到该资源');
            except exceptions.ArgsException as message:
                await window_warn_big_2(str(message));
            except ErrorCountsTooMuch as e:
                await window_warn(str(e));
                break;
            except ErrorCredential as e:
                await window_warn(str(e));
                break;
            except:
                await window_warn(f'错误: {sys.exc_info()[0]}, {sys.exc_info()[1]}');
                break;
        elif get[0] == 1:
            tmp = await start_settings();
            if tmp:
                break;
            del tmp;


if __name__ == '__main__':
    ver = '0.10.4';
    if not os.path.exists('./Download'):
        os.mkdir('./Download');
    programPath = os.getcwd();
    path = getUserData('downloadPath');
    if path is None:
        os.chdir('./Download');
    else:
        os.chdir(path);
    del path
    PID = os.getpid();
    window_setVar(PID, programPath);
    asyncio.get_event_loop().run_until_complete(Main());
    os.kill(PID, 15);
