# Copyright (c) Majjcom 2021
from multiprocessing import cpu_count
from .utils import sizefstr
from typing import List
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


class DownloadBook:
    def __init__(self, _id, tempf, state, url, headers, length, process, retry):
        self.id: int = _id
        self.tempfile = tempf
        self.state: int = state
        self.url: str = url
        self.headers: dict = headers
        self.length: int = length
        self.process: int = process
        self.retry: int = retry


class PieceDownload(threading.Thread):
    def __init__(self, book: DownloadBook, tempDir: tempfile.TemporaryDirectory):
        super().__init__()
        book.state = 1
        self._book = book
        self._tempDir = tempDir

    def run(self) -> None:
        asyncio.new_event_loop().run_until_complete(download_piece(self._book, self._tempDir))


class CopyerBasket:
    def __init__(self, tasks_: list):
        self.tasks: List[DownloadBook] = tasks_
        self._copyFinished = False

    def isFinished(self):
        return self._copyFinished

    def copyfinish(self) -> None:
        self._copyFinished = True
        return None


class Copyer(threading.Thread):
    def __init__(self, basket_: CopyerBasket, targetName: str):
        super().__init__()
        self._basket = basket_
        self._targetName = targetName
        self._fp = open(targetName, 'wb+')

    def run(self) -> None:
        runFinished = False
        while not runFinished:
            count = 0
            for book in self._basket.tasks:
                if book.state == 2:
                    count += 1
                    if not book.tempfile.closed:
                        while True:
                            chunk = book.tempfile.read(1024)
                            if not chunk:
                                break
                            self._fp.write(chunk)
                        book.tempfile.close()
                else:
                    break
                if count == len(self._basket.tasks):
                    runFinished = True
            time.sleep(0.1)
        self._basket.copyfinish()
        self._fp.close()


async def download_with_threads(url: str, v, name: str = 'Download', headers: dict = None, max_thread_count: int = cpu_count(), piece_per_size: int = 512 * 1024 ** 2):
    if headers is None:
        headers = {}
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=headers) as resp:
            totalLength = int(resp.headers.get('content-length'))
    pieces = totalLength // piece_per_size
    byteMore = totalLength % piece_per_size
    tempDir = tempfile.TemporaryDirectory(prefix='TEMP', dir='.')

    def creatBook(end: bool = False):
        book_headers = copy.deepcopy(headers)
        book_headers['range'] = 'bytes={}-{}'.format(i * piece_per_size, '' if end else (i + 1) * piece_per_size - 1)

        book = DownloadBook(
            _id=i,
            tempf=tempfile.TemporaryFile('w+b', dir=tempDir.name),
            state=0,    # -1: 失败, 0: 未开始, 1: 进行中, 2: 已完成
            url=url,
            headers=book_headers,
            length=byteMore if end else piece_per_size,
            process=0,
            retry=0
        )
        tasks.append(book)

    tasks = list()
    i = 0
    for i in range(pieces):
        creatBook()
    i = 0 if pieces == 0 else i + 1
    if byteMore != 0:
        creatBook(True)

    copyertbasket = CopyerBasket(tasks)
    copyer = Copyer(copyertbasket, name)
    copyer.start()

    while True:
        j = 0
        running = 0
        for i in tasks:
            if i.state == 2:
                j += 1
            elif i.state == 1:
                running += 1
        if j == len(tasks):
            break
        for i in tasks:
            if i.state <= 0 and running < max_thread_count:
                if i.retry <= 3:
                    tmp = PieceDownload(i, tempDir)
                    tmp.start()
                    running += 1
                else:
                    raise ErrorDownloadError('文件下载失败: 片段 {}'.format(i['id']))
        process = 0
        for i in tasks:
            process += i.process
        v[3].set(
            '{} / {} {}%'.format(
                sizefstr.sizefStr(process),
                sizefstr.sizefStr(totalLength),
                round(process / totalLength * 100, 2)
            )
        )
        v[4].set(process / totalLength * 100)
        time.sleep(0.1)
    while True:
        if copyertbasket.isFinished():
            break
        time.sleep(0.1)
    tempDir.cleanup()
    return


async def download_piece(book, tempDir: tempfile.TemporaryDirectory):
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(book.url, headers=book.headers) as resp:
                # totalLength = int(resp.headers.get('content-length'))
                while True:
                    chunk = await resp.content.read(1024)
                    book.process += len(chunk)
                    if not chunk:
                        break
                    book.tempfile.write(chunk)
        book.state = 2
        book.tempfile.seek(0)
    except:
        book.process = 0
        book.retry += 1
        book.state = -1
        book.tempfile.close()
        book.tempfile = tempfile.TemporaryFile('w+b', dir=tempDir.name)
    return

