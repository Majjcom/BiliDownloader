# Copyright (c) Majjcom 2021
from .utils import sizefstr
import threading
import tempfile
import aiohttp
import asyncio
import copy
import time


class ErrorDownloadError(Exception):
    def __init__(self, info: str):
        super().__init__()
        self._info = info

    def __str__(self):
        return self._info


class PieceDownload(threading.Thread):
    def __init__(self, book: dict):
        super().__init__()
        book['state'] = 1
        self.__book = book

    def run(self) -> None:
        asyncio.new_event_loop().run_until_complete(download_piece(self.__book))


async def download_with_threads(url: str, v, name: str = 'Download', headers: dict = None, max_thread_count: int = 4, piece_per_size: int = 512 * 1024 ** 2):
    if headers is None:
        headers = {}
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=headers) as resp:
            totalLength = int(resp.headers.get('content-length'))
    pieces = totalLength // piece_per_size
    byteMore = totalLength % piece_per_size
    tempDir = tempfile.TemporaryDirectory(prefix='TEMP', dir='.')

    def creatBook(end: bool = False):
        book = dict()
        book['id'] = i
        book['tempFile'] = tempfile.TemporaryFile('w+b', dir=tempDir.name)
        book['state'] = 0
        book['url'] = url
        book_headers = copy.deepcopy(headers)
        book_headers['range'] = 'bytes={}-{}'.format(i * piece_per_size, '' if end else (i + 1) * piece_per_size - 1)
        book['headers'] = book_headers
        book['length'] = byteMore if end else piece_per_size
        book['process'] = 0
        book['state'] = 0
        book['retry'] = 0
        tasks.append(book)

    tasks = list()
    i = 0
    for i in range(pieces):
        creatBook()
    i = 0 if pieces == 0 else i + 1
    if byteMore != 0:
        creatBook(True)
    while True:
        j = 0
        running = 0
        for i in tasks:
            if i['state'] == 2:
                j += 1
            elif i['state'] == 1:
                running += 1
        if j == len(tasks):
            break
        for i in tasks:
            if i['state'] <= 0 and running < max_thread_count:
                if i['retry'] <= 3:
                    tmp = PieceDownload(i)
                    tmp.start()
                    running += 1
                else:
                    raise ErrorDownloadError('文件下载失败: 片段 {}'.format(i['id']))
        process = 0
        for i in tasks:
            process += i['process']
        v[3].set('{} / {} {}%'.format(sizefstr.sizefStr(process), sizefstr.sizefStr(totalLength), round(process / totalLength * 100, 2)))
        v[4].set(process / totalLength * 100)
        time.sleep(0.1)
    with open(name, 'wb') as f:
        for i in tasks:
            while True:
                chunk = i['tempFile'].read(1024)
                if not chunk:
                    break
                f.write(chunk)
            i['tempFile'].close()
    tempDir.cleanup()
    return


async def download_piece(book):
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(book['url'], headers=book['headers']) as resp:
                totalLength = int(resp.headers.get('content-length'))
                while True:
                    chunk = await resp.content.read(1024)
                    book['process'] += len(chunk)
                    if not chunk:
                        break
                    book['tempFile'].write(chunk)
        book['tempFile'].seek(0)
        book['state'] = 2
    except:
        book['retry'] += 1
        book['state'] = -1
