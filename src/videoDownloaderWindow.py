# Copyright © 2021 BiliDownloader
# Made by Majjcom
from bilibili_api import Credential, video, bangumi, exceptions
from window import *
import subprocess
import aiohttp
import asyncio
import time
import sys
import os

class ErrorCountsTooMuch(Exception):
    def __init__(self, info : str = None):
        Exception.__init__(self);
        self.info : str = info;
    def __str__(self):
        return self.info;

async def downloadVideo(Url : dict, id : int, v, name : str = 'video'):
    global mainprocess;
    async with aiohttp.ClientSession() as sess:
        video_url = Url['dash']['video'][0]['baseUrl'];
        for i in Url['dash']['video']:
            if i['codecid'] == 7:
                if i['id'] == id:
                    video_url = i['baseUrl'];
        HEADERS = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bilibili.com/'
        };
        async with sess.get(video_url, headers=HEADERS) as resp:
            length = resp.headers.get('content-length');
            with open(f'{name}_temp.mp4', 'wb') as f:
                process = 0;
                count = 0;
                while True:
                    chunk = await resp.content.read(1024);
                    count += 1;
                    process += len(chunk);
                    if not chunk:
                        v[4].set(round(process / int(length) * 100, 2));
                        f.close();
                        await sess.close();
                        break;
                    if count % 512 == 0:
                        percent = round(process / int(length) * 100, 2);
                        v[3].set(f'{process} / {length} {percent}%');
                        v[4].set(percent);
                    f.write(chunk);


async def downloadAudio(Url : dict, id : int, v, name : str = 'audio'):
    global mainprocess;
    async with aiohttp.ClientSession() as sess:
        audio_url = Url['dash']['audio'][0]['baseUrl'];
        HEADERS = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bilibili.com/'
        };
        async with sess.get(audio_url, headers=HEADERS) as resp:
            length = resp.headers.get('content-length');
            with open(f'{name}_temp.m4a', 'wb') as f:
                process = 0;
                count = 0;
                while True:
                    chunk = await resp.content.read(1024);
                    count += 1;
                    process += len(chunk);
                    if not chunk:
                        v[4].set(round(process / int(length) * 100, 2));
                        f.close();
                        await sess.close();
                        break;
                    if count % 512 == 0 or process == length:
                        percent = round(process / int(length) * 100, 2);
                        v[3].set(f'{process} / {length} {percent}%');
                        v[4].set(percent);
                    f.write(chunk);


async def GetCredential():
    url = 'http://d.majjcom.site:1288/text/credential';
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            got = b'';
            while True:
                chunk = await resp.content.read(1024);
                if not chunk:
                    await sess.close();
                    break;
                got += chunk;
            got_d = got.decode('utf-8');
            if len(got_d) == 0 or got_d == 'none':
                return None;
            got_cut = got.decode('utf-8').split('\n');
            crd = Credential(sessdata=got_cut[0], bili_jct=got_cut[1], buvid3=got_cut[2]);
            return crd;


async def checkUpdate():
    url = 'http://d.majjcom.site:1288/text/ver';

    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            ver = await resp.content.read(1024);
            await sess.close();
            return ver.decode();


def ifuptodate(a: str, b: str) -> bool:
    a_s = a.split('.');
    b_s = b.split('.');
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
    url = f'http://d.majjcom.site:1288/file/{name}';
    arg : list = list();
    arg.append(False);
    win = window_updating(arg);
    win.start();
    time.sleep(0.5);
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
                arg[0] = True;
                time.sleep(0.3);
                os.system(name);
                time.sleep(0.2);
                global PID;
                os.kill(PID, 15);



async def videoDown(vid_id : str, credential = None):
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
        if haveCred:
            v = video.Video(bvid=vid_ID, credential=credential);
        else:
            v = video.Video(bvid=vid_ID);
    else:
        if haveCred:
            v = video.Video(aid=vid_ID, credential=credential);
        else:
            v = video.Video(aid=vid_ID);
    vid_info = await v.get_info();
    vid_pages = await v.get_pages();
    del v;
    while True:
        tmp = await window_confirm('请确认视频:\n\n标题: {}\nUP主: {}'.format(vid_info['title'], vid_info['owner']['name']));
        if tmp:
            break;
        else:
            await window_warn('退出...');
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
    urls : dict = dict();
    arg = list();
    arg.append(False);
    tmp = window_geturl(arg);
    tmp.start();
    time.sleep(0.5);
    for key in vid_chose_c:
        arg[1].set('正在获取 {} 的链接'.format(key));
        if vid_id_isBV:
            if haveCred:
                v = video.Video(bvid=vid_ID, credential=credential);
            else:
                v = video.Video(bvid=vid_ID);
        else:
            if haveCred:
                v = video.Video(aid=vid_ID, credential=credential);
            else:
                v = video.Video(aid=vid_ID);
        while True:
            try:
                time.sleep(0.3);
                url = await v.get_download_url(cid=key);
                break;
            except:
                pass;
        del v;
        name = '{}_{}_{}'.format(vid_info['title'].replace(' ', '_'), vid_chose_c[key]['page'], vid_chose_c[key]['part'].replace(' ', '_'));
        urls[name] = url;
    arg[0] = True;
    time.sleep(0.5);
    del tmp;
    del arg;

    for name in urls:
        vid_quality_list = urls[name]['accept_quality'];
        break;

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
    for name in urls:
        arg[1].set('开始下载 {}'.format(name));
        retry = 0;
        while True:
            try:
                arg[2].set('下载视频流');
                arg[5]['mode'] = 'determinate';
                await downloadVideo(urls[name], vid_quality, arg, name);
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
                arg[2].set('下载音频流');
                arg[5]['mode'] = 'determinate';
                await downloadAudio(urls[name], 0, arg, name);
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
        subprocess.run(('../ffmpeg/ffmpeg',
                        '-i', '{}_temp.mp4'.format(name),
                        '-i', '{}_temp.m4a'.format(name),
                        '-vcodec', 'copy',
                        '-acodec', 'copy',
                        '{}.mp4'.format(name)),
                       stdout=DEV_NULL, stderr=subprocess.STDOUT);
        DEV_NULL.close();
        del DEV_NULL;
        arg[2].set('合并完成');
        arg[5].stop();
        os.remove('{}_temp.mp4'.format(name));
        os.remove('{}_temp.m4a'.format(name));
        arg[1].set('{} 下载完成'.format(name));
        time.sleep(0.5);
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
        tmp = await window_confirm(f'请确认番剧:\n\n标题: {vid_info["media"]["title"]}\n评分: {vid_info["media"]["rating"]["score"]}');
        if tmp:
            break;
        else:
            await window_warn('退出...');
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
        while True:
            try:
                i['url'] = await v.get_download_url(cid=i['cid']);
                break;
            except:
                time.sleep(0.3);
        del v;
    arg[0] = True;
    time.sleep(0.5);
    del tmp;
    del arg;
    vid_quality_list = vid_chose_c[0]['url']['accept_quality'];
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
        subprocess.run(('../ffmpeg/ffmpeg',
                        '-i', '{}_temp.mp4'.format(name),
                        '-i', '{}_temp.m4a'.format(name),
                        '-vcodec', 'copy',
                        '-acodec', 'copy',
                        '{}.mp4'.format(name)),
                       stdout=DEV_NULL, stderr=subprocess.STDOUT);
        DEV_NULL.close();
        del DEV_NULL;
        arg[2].set('合并完成');
        arg[5].stop();
        os.remove('{}_temp.mp4'.format(name));
        os.remove('{}_temp.m4a'.format(name));
        arg[1].set('{} 下载完成'.format(name));
        time.sleep(0.5);
    arg[0] = True;
    time.sleep(0.5);
    del arg;
    del tmp;
    await window_finish(os.getcwd());
    return;


async def Main():
    global ver;
    global PID;
    available : tuple = ('bv', 'av', 'md');
    try:
        ver_get = await checkUpdate();
        if not ifuptodate(ver, ver_get):
            await window_showupdate();
            await getUpdate(ver_get);
    except:
        pass;
    # Bilibili Account Credential
    try:
        credential = await GetCredential();
    except:
        await window_warn('网络错误...(如果你的网络正常，可能是作者的服务器挂了...)');
        os.kill(PID, 15);
    haveCred : bool = None;
    if credential:
        haveCred = True;
    else:
        haveCred = False
    mode = 'none';
    while True:
        while True:
            vid_id = await window_ask();
            if vid_id[:2].lower() in available:
                if vid_id[:2].lower() == 'md':
                    mode = 'bangumi';
                    break;
                elif vid_id[:2].lower() == 'bv' or vid_id[:2].lower() == 'av':
                    mode = 'video';
                    break;
            else:
                await window_warn('请输入正确的值...');
        try:
            if mode == 'bangumi':
                if haveCred:
                    await bangumiDown(vid_id, credential);
                else:
                    await bangumiDown(vid_id);
            elif mode == 'video':
                if haveCred:
                    await videoDown(vid_id, credential);
                else:
                    await videoDown(vid_id);
            break;
        except exceptions.ResponseCodeException:
            await window_warn('404，未找到该资源');
        except exceptions.ArgsException as message:
            await window_warn_big_2(str(message));
        except ErrorCountsTooMuch as e:
            await window_warn(str(e));
            break;
        except:
            await window_warn(f'错误: {sys.exc_info()[1]}');
            break;


if __name__ == '__main__':
    ver = '0.8.4';
    if not os.path.exists('./Download'):
        os.mkdir('./Download');
    os.chdir('./Download');
    PID = os.getpid();
    asyncio.get_event_loop().run_until_complete(Main());
    os.kill(PID, 15);
