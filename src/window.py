from tkinter import ttk, messagebox, font, filedialog
from PIL import Image, ImageTk
import http.client as hcl
from typing import Union
from urllib import parse
import tkinter as tk
import webbrowser
import threading
import pyperclip
import winsound
import time
import os


async def window_warn(text : str, playSound : bool = True, level : str = '警告'):
    if playSound:
        winsound.PlaySound('SystemAsterisk', winsound.SND_ASYNC)
    win = tk.Tk()
    win.title('BiliDownloader-{}'.format(level))
    win.geometry('395x122+200+200')
    win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
    win.resizable(tk.FALSE, tk.FALSE)
    #f = font.Font(root=win, name='TkTextFont', exists=True)
    f = font.Font(root=win, family='HarmonyOS Sans SC')
    f['size'] = 11
    btnStyle = ttk.Style(win)
    btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
    mainframe = ttk.Frame(win, padding=5)
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    textframe = ttk.Frame(mainframe)
    textframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W))
    tex0 = tk.Text(textframe, width=41, height=4, font=f);
    tex0.pack(fill=tk.BOTH, side=tk.LEFT)
    sba0 = ttk.Scrollbar(textframe)
    sba0.pack(fill=tk.Y, side=tk.RIGHT)
    sba0.config(command=tex0.yview)
    tex0.config(yscrollcommand=sba0.set)
    tex0.insert(tk.END, text)
    tex0.config(state=tk.DISABLED)
    btnframe = ttk.Frame(mainframe)
    btnframe.grid(column=0, row=1)
    def btn0Callback(e=None):
        win.destroy()
    btn0 = ttk.Button(btnframe, text='确认', command=btn0Callback, style='TButton')
    btn0.pack(side=tk.TOP)
    win.bind('<Key-Return>', btn0Callback)
    win.mainloop()
    return


async def window_ask() -> tuple:
    global retv
    retv = 'a'
    win = tk.Tk()
    win.title('BiliDownloader')
    win.geometry('395x112+200+200')
    win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
    win.resizable(tk.FALSE, tk.FALSE)
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno')
        if tmp:
            global PID
            os.kill(PID, 15)
    win.protocol('WM_DELETE_WINDOW', showmessage)
    f = font.Font(root=win, family='HarmonyOS Sans SC')
    f['size'] = 11
    btnStyle = ttk.Style(win)
    btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
    mainframe = ttk.Frame(win, padding=5)
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    lab0 = ttk.Label(mainframe, text='请输入视频链接或视频的BV号、AV号、MD号、EP号\n(包含开头的BV、AV、MD和EP):', font=f)
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W))
    text = tk.Variable(win)
    etr0 = ttk.Entry(mainframe, width=42, textvariable=text, font=f)
    etr0.grid(column=1, row=2, sticky=(tk.N, tk.W))
    def callback0(e=None):
        global retv
        retv = (0, text.get())
        win.destroy()
    def callback1():
        global retv
        retv = (1, 'set')
        win.destroy()
    def callback2(e):
        text.set(pyperclip.paste())
    etr0.bind('<Button-3>', callback2)
    etr0.bind('<Key-Return>', callback0)
    fra0 = ttk.Frame(mainframe)
    fra0.grid(column=1, row=3, sticky=(tk.E), pady=1)
    btn0 = ttk.Button(fra0, text='OK', command=callback0, style='TButton')
    btn0.grid(column=2, row=1, sticky=(tk.E))
    btn1 = ttk.Button(fra0, text='设置', command=callback1, style='TButton')
    btn1.grid(column=1, row=1, sticky=(tk.E))
    win.mainloop()
    return retv


async def window_settings(downloadP: str, haveC: Union[int, None], isReserveAudio: bool, isSaveDanmaku: bool):
    global retv
    retv = None
    win = tk.Tk()
    win.title('BiliDownloader')
    win.geometry('395x174+200+200')
    win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
    win.resizable(tk.FALSE, tk.FALSE)
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno')
        if tmp:
            global PID
            os.kill(PID, 15)
    win.protocol('WM_DELETE_WINDOW', showmessage)
    f = font.Font(root=win, family='HarmonyOS Sans SC')
    f['size'] = 11
    btnStyle = ttk.Style(win)
    btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
    chkStyle = ttk.Style(win)
    chkStyle.configure('TCheckbutton', font=('HarmonyOS Sans SC', 11))
    mainframe = ttk.Frame(win, padding=5)
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    labf0 = ttk.Labelframe(mainframe, text='设置')
    labf0.grid(column=1, row=1, sticky=(tk.N, tk.W, tk.E))
    def callback0():
        global retv
        retv = (0, filedialog.askdirectory(parent=win, title='选择下载路径'))
        win.destroy()
    btn0 = ttk.Button(labf0, text='设置下载位置', command=callback0, style='TButton')
    btn0.grid(column=1, row=1, sticky=(tk.W))
    v0 = tk.Variable(win)
    v0.set(downloadP)
    etn0 = ttk.Entry(labf0, textvariable=v0, state='readonly', width=29, font=f)
    etn0.grid(column=2, row=1, sticky=(tk.W))
    def callback1():
        global retv
        retv = (1,)
        win.destroy()
    btn1 = ttk.Button(labf0, text='登录b站', command=callback1, style='TButton')
    btn1.grid(column=1, row=2, sticky=(tk.W))
    v1 = tk.Variable(win)
    v1.set('未登录' if haveC is None else '已登录' if haveC > 0 else '已登录-登录已过期')
    etn1 = ttk.Entry(labf0, textvariable=v1, state='readonly', width=29, font=f)
    etn1.grid(column=2, row=2, sticky=(tk.W))
    v2 = tk.BooleanVar(win, value=isReserveAudio)
    chk0 = ttk.Checkbutton(labf0, text='保留下载的音频文件', variable=v2, style='TCheckbutton')
    chk0.grid(column=2, row=3, sticky=(tk.W))
    v3 = tk.BooleanVar(win, value=isSaveDanmaku)
    chk1 = ttk.Checkbutton(labf0, text='下载弹幕', variable=v3, style='TCheckbutton')
    chk1.grid(column=2, row=4, sticky=(tk.W))
    fra0 = ttk.Frame(mainframe)
    fra0.grid(column=1, row=2, pady=1)
    def callback2():
        global retv
        retv = (3,v2.get(), v3.get())
        win.destroy()
    btn2 = ttk.Button(fra0, text='返回', command=callback2, style='TButton')
    btn2.grid(column=1, row=1)
    def callback3():
        tmp = messagebox.askyesno(title='确认', message='确认重置?', parent=win, type='yesno')
        if tmp:
            global retv
            retv = (2,)
            win.destroy()
    btn3 = ttk.Button(fra0, text='重置', command=callback3, style='TButton')
    btn3.grid(column=2, row=1)
    def callback4():
        webbrowser.open('https://gitee.com/majjcom/bili-downloader/blob/master/README.md')
    btn4 = ttk.Button(fra0, text='帮助', command=callback4, style='TButton')
    btn4.grid(column=3, row=1)
    win.mainloop()
    return retv


async def window_showupdate_detal(info: str):
    win = tk.Tk()
    win.title('BiliDownloader-更新信息')
    win.geometry('395x302+200+200')
    win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
    win.resizable(tk.FALSE, tk.FALSE)
    f = font.Font(root=win, family='HarmonyOS Sans SC')
    f['size'] = 11
    btnStyle = ttk.Style(win)
    btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
    mainframe = ttk.Frame(win, padding=5)
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    textframe = ttk.Frame(mainframe)
    textframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W))
    tex0 = tk.Text(textframe, width=41, height=13, font=f);
    tex0.pack(fill=tk.BOTH, side=tk.LEFT)
    sba0 = ttk.Scrollbar(textframe)
    sba0.pack(fill=tk.Y, side=tk.RIGHT)
    sba0.config(command=tex0.yview)
    tex0.config(yscrollcommand=sba0.set)
    tex0.insert(tk.END, info)
    tex0.config(state=tk.DISABLED)
    btnframe = ttk.Frame(mainframe)
    btnframe.grid(column=0, row=1)
    def btn0Callback(e=None):
        win.destroy()
    btn0 = ttk.Button(btnframe, text='确认', command=btn0Callback, style='TButton')
    btn0.pack(side=tk.TOP)
    win.bind('<Key-Return>', btn0Callback)
    win.mainloop()
    return


async def window_showupdate():
    win = tk.Tk()
    win.title('BiliDownloader')
    win.geometry('395x85+200+200')
    win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
    win.resizable(tk.TRUE, tk.FALSE)
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno')
        if tmp:
            win.destroy()
    win.protocol('WM_DELETE_WINDOW', showmessage)
    f = font.Font(root=win, family='HarmonyOS Sans SC')
    f['size'] = 11
    btnStyle = ttk.Style(win)
    btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
    mainframe = ttk.Frame(win, padding=5)
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    lab0 = ttk.Label(mainframe, text='有新的版本更新，即将开始下载\nP.S. 如果出现多次更新错误，可以下载软件包获取更新', font=f)
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W))
    def callback(e=None):
        win.destroy()
    win.bind('<Key-Return>', callback)
    btn0 = ttk.Button(mainframe, text='OK', command=callback, style='TButton')
    btn0.grid(column=1, row=2, sticky=(tk.S, tk.W))
    win.mainloop()
    return


async def window_confirm(text : str, cover_url: str):
    global retv, ifPathSet
    ifPathSet = None
    retv = False
    win = tk.Tk()
    win.title('BiliDownloader')
    win.geometry('395x164+200+200')
    win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
    win.resizable(tk.FALSE, tk.FALSE)
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno')
        if tmp:
            global PID
            os.kill(PID, 15)
    win.protocol('WM_DELETE_WINDOW', showmessage)
    f = font.Font(root=win, family='HarmonyOS Sans SC')
    f['size'] = 11
    btnStyle = ttk.Style(win)
    btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
    mainframe = ttk.Frame(win, padding=5)
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.S, tk.W))
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    t = tk.Variable(win)
    t.set(text)
    lab0 = ttk.Label(mainframe, textvariable=t, font=f)
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W))
    def callback0(e=None):
        global retv
        retv = True
        win.destroy()
    def callback1():
        win.destroy()
    def callback2():
        global programPath
        subwin = tk.Toplevel(master=win)
        subwin.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
        subwin.resizable(tk.FALSE, tk.FALSE)
        url = parse.urlsplit(cover_url)
        extion_name = os.path.splitext(url.path)[1]
        con = hcl.HTTPSConnection(url.hostname)
        con.request('GET', url.path)
        resp = con.getresponse()
        readed = resp.read()
        img_path = os.path.join(programPath, 'data/cover' + str(int(time.time())) + extion_name)
        fp = open(img_path, 'wb')
        fp.write(readed)
        resp.close()
        con.close()
        fp.close()
        img0 = Image.open(img_path)
        if img0.size[0] > 720:
            precent = 720 / img0.size[0]
            img0 = img0.resize((720, int(float(img0.size[1]) * precent)), Image.ANTIALIAS)
        pic0 = ImageTk.PhotoImage(master=subwin, image=img0)
        fra0 = ttk.Frame(master=subwin)
        fra0.grid(column=1, row=1, sticky=(tk.N, tk.E, tk.S, tk.W))
        lab0 = tk.Label(master=fra0, image=pic0)
        lab0.pack(fill=tk.BOTH, side=tk.TOP)
        def close():
            img0.close()
            if os.path.exists(img_path):
                os.remove(img_path)
            subwin.destroy()
        subwin.protocol('WM_DELETE_WINDOW', close)
        subwin.mainloop()
    win.bind('<Key-Return>', callback0)
    fra0 = ttk.Frame(mainframe)
    fra0.grid(column=1, row=2, sticky=(tk.W))
    btn0 = ttk.Button(fra0, text='YES', command=callback0, style='TButton')
    btn0.grid(column=1, row=1, sticky=(tk.W))
    btn1 = ttk.Button(fra0, text='NO', command=callback1, style='TButton')
    btn1.grid(column=2, row=1, sticky=(tk.W))
    btn2 = ttk.Button(fra0, text='查看封面', command=callback2, style='TButton')
    btn2.grid(column=3, row=1, sticky=(tk.W))
    win.mainloop()
    return retv


async def window_config_p(count : int):
    global retv
    retv = ''
    win = tk.Tk()
    win.title('BiliDownloader')
    win.geometry('395x115+200+200')
    win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
    win.resizable(tk.FALSE, tk.FALSE)
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno')
        if tmp:
            global PID
            os.kill(PID, 15)
    win.protocol('WM_DELETE_WINDOW', showmessage)
    f = font.Font(root=win, family='HarmonyOS Sans SC')
    f['size'] = 11
    btnStyle = ttk.Style(win)
    btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
    mainframe = ttk.Frame(win, padding=5)
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.S, tk.W))
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    t0 = tk.Variable(win)
    t0.set('分P列表中共有{}个视频'.format(count))
    lab0 = ttk.Label(mainframe, textvariable=t0, font=f)
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W))
    lab1 = ttk.Label(mainframe, text='请选择下载范围, 用","分隔(如1-1或1-5或1-1, 3-5): ', font=f)
    lab1.grid(column=1, row=2, sticky=(tk.W))
    t1 = tk.Variable(win)
    t1.set('1-{}'.format(count))
    etr0 = ttk.Entry(mainframe, textvariable=t1, font=f)
    etr0.grid(column=1, row=3, sticky=(tk.W))
    def callback(e=None):
        global retv
        retv = t1.get()
        win.destroy()
    etr0.bind('<Key-Return>', callback)
    btn0 = ttk.Button(mainframe, text='OK', command=callback, style='TButton')
    btn0.grid(column=1, row=4, sticky=(tk.W, tk.S))
    win.mainloop()
    return retv


async def window_config_q(tip : str):
    global retv
    retv = ''
    win = tk.Tk()
    win.title('BiliDownloader')
    win.geometry('395x92+200+200')
    win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
    win.resizable(tk.FALSE, tk.FALSE)
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno')
        if tmp:
            global PID
            os.kill(PID, 15)
    def showHelp():
        messagebox.showinfo(title='提示',
                            parent=win,
                            message='提示:\n\n'
                                    '120\t4K\n116\t1080p60\n112\t1080p+\n80\t1080p\n72\t720p60\n64\t720p\n32\t480p\n16\t320p\n\n'
                                    '如果出现一直无法下载的情况可以稍微降低清晰度哦ლ(´ڡ`ლ)\n'
                                    '部分会员资源下载需要设置通行证，请自行到设置中进行设置\n\n'
                                    'P.S.现已支持4k分辨率视频下载!!!')
    win.protocol('WM_DELETE_WINDOW', showmessage)
    f = font.Font(root=win, family='HarmonyOS Sans SC')
    f['size'] = 11
    btnStyle = ttk.Style(win)
    btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
    mainframe = ttk.Frame(win, padding=5)
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    lab0 = ttk.Label(mainframe, text='请选择清晰度(可选: {}): '.format(tip), font=f)
    lab0.grid(column=1, row=1, stick=(tk.N, tk.W))
    t0 = tk.Variable(win)
    t0.set(tip.split(', ', 1)[0])
    etr0 = ttk.Entry(mainframe, textvariable=t0, width=10, font=f)
    etr0.grid(column=1, row=2, sticky=(tk.W))
    def callback(e=None):
        global retv
        retv = t0.get()
        win.destroy()
    etr0.bind('<Key-Return>', callback)
    fra0 = ttk.Frame(mainframe)
    fra0.grid(column=1, row=3, sticky=(tk.W), pady=2)
    btn0 = ttk.Button(fra0, text='OK', command=callback, style='TButton')
    btn0.grid(column=1, row=1, sticky=(tk.W))
    btn1 = ttk.Button(fra0, text='提示', command=showHelp, style='TButton')
    btn1.grid(column=2, row=1, sticky=(tk.W))
    win.mainloop()
    return retv


async def window_finish(text):
    win = tk.Tk()
    win.title('BiliDownloader')
    win.geometry('395x90+200+200')
    win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
    win.resizable(tk.FALSE, tk.FALSE)
    f = font.Font(root=win, family='HarmonyOS Sans SC')
    f['size'] = 11
    btnStyle = ttk.Style(win)
    btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
    mainframe = ttk.Frame(win, padding=5)
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    lab0 = ttk.Label(mainframe, text='视频全部下载完成，保存在: ', font=f)
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W))
    t0 = tk.Variable(win)
    t0.set(text)
    etr0 = ttk.Entry(mainframe, textvariable=t0, state='readonly', width=30, font=f)
    etr0.grid(column=1, row=2, sticky=(tk.W))
    def callback0():
        win.destroy()
    btnFrame = ttk.Frame(mainframe)
    btnFrame.grid(column=1, row=3, sticky=(tk.S, tk.W))
    btn0 = ttk.Button(btnFrame, text='OK', command=callback0, style='TButton')
    btn0.grid(column=1, row=1)
    def callback1():
        os.startfile(text, 'explore')
    btn1 = ttk.Button(btnFrame, text='打开目录', command=callback1, style='TButton')
    btn1.grid(column=2, row=1)
    win.mainloop()
    return


class window_interrupt(threading.Thread):
    def __init__(self, this : tk.Tk, v):
        threading.Thread.__init__(self)
        self._this = this
        self._v = v

    def run(self):
        while True:
            time.sleep(0.1)
            if self._v[0]:
                self._this.destroy()
                return

class window_geturl(threading.Thread):
    def __init__(self, v):
        threading.Thread.__init__(self)
        self._v = v # 0: isRun, 1: t0

    def run(self) -> None:
        win = tk.Tk()
        win.title('BiliDownloader')
        win.geometry('395x35+200+200')
        win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
        win.resizable(tk.FALSE, tk.FALSE)
        def showmessage():
            tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno')
            if tmp:
                global PID
                os.kill(PID, 15)
        win.protocol('WM_DELETE_WINDOW', showmessage)
        f = font.Font(root=win, family='HarmonyOS Sans SC')
        f['size'] = 11
        btnStyle = ttk.Style(win)
        btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
        mainframe = ttk.Frame(win, padding=5)
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)
        t0 = tk.Variable(win)
        t0.set('null')
        self._v.append(t0)
        lab0 = ttk.Label(mainframe, textvariable=t0, font=f)
        lab0.grid(column=1, row=1, sticky=(tk.N, tk.W))
        tmp = window_interrupt(win, self._v)
        tmp.start()
        win.mainloop()
        return


class window_downloas(threading.Thread):
    def __init__(self, v):
        threading.Thread.__init__(self)
        self._v = v # 0: isRun, 1: t0, 2: t1, 3: t2, 4: t3, 5: bar

    def run(self) -> None:
        win = tk.Tk()
        win.title('BiliDownloader')
        win.geometry('395x105+200+200')
        win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
        win.resizable(tk.FALSE, tk.FALSE)
        def showmessage():
            messagebox.showwarning('警告', '请不要关闭这个窗口...', parent=win)
        win.protocol('WM_DELETE_WINDOW', showmessage)
        f = font.Font(root=win, family='HarmonyOS Sans SC')
        f['size'] = 11
        btnStyle = ttk.Style(win)
        btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
        mainframe = ttk.Frame(win, padding=5)
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)
        t0 = tk.Variable(win)
        t0.set('null')
        self._v.append(t0)
        lab0 = ttk.Label(mainframe, textvariable=t0, font=f)
        lab0.grid(column=1, row=1, sticky=(tk.N, tk.W))
        t1 = tk.Variable(win)
        t1.set('null')
        self._v.append(t1)
        lab1 = ttk.Label(mainframe, textvariable=t1, font=f)
        lab1.grid(column=1, row=2, sticky=(tk.W))
        t2 = tk.Variable(win)
        t2.set('null')
        self._v.append(t2)
        lab2 = ttk.Label(mainframe, textvariable=t2, font=f)
        lab2.grid(column=1, row=3, sticky=(tk.W))
        t3 = tk.Variable(win)
        t3.set(0.0)
        self._v.append(t3)
        bar0 = ttk.Progressbar(
                mainframe,
                orient=tk.HORIZONTAL,
                length=250,
                mode='determinate',
                variable=t3
            )
        bar0.grid(column=1, row=4, sticky=(tk.S, tk.W))
        self._v.append(bar0)
        tmp = window_interrupt(win, self._v)
        tmp.start()
        win.mainloop()
        return


class window_updating(threading.Thread):
    def __init__(self, arg : list):
        threading.Thread.__init__(self)
        self._arg = arg

    def run(self):
        win = tk.Tk()
        win.title('BiliDownloader Update')
        win.geometry('395x60+200+200')
        win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
        win.resizable(tk.FALSE, tk.FALSE)
        def showmessage():
            messagebox.showwarning('警告', '请不要关闭这个窗口...', parent=win)
        win.protocol('WM_DELETE_WINDOW', showmessage)
        f = font.Font(root=win, family='HarmonyOS Sans SC')
        f['size'] = 11
        btnStyle = ttk.Style(win)
        btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
        mainframe = ttk.Frame(win, padding=5)
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)
        lab0 = ttk.Label(mainframe, text='正在下载更新...', font=f)
        lab0.grid(column=1, row=1, sticky=(tk.W, tk.N))
        t0 = tk.Variable(win)
        t0.set(0.0)
        self._arg.append(t0)
        bar0 = ttk.Progressbar(
            mainframe,
            orient=tk.HORIZONTAL,
            length=250,
            mode='determinate',
            variable=t0
        )
        bar0.grid(column=1, row=2, sticky=(tk.W, tk.S))
        tmp = window_interrupt(win, self._arg)
        tmp.start()
        win.mainloop()

class window_checkUpdate(threading.Thread):
    def __init__(self, basket : list):
        threading.Thread.__init__(self)
        self._basket = basket

    def run(self):
        global haveFont
        win = tk.Tk()
        win.title('BiliDownloader Update')
        win.geometry('395x112+200+200')
        win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
        win.resizable(tk.FALSE, tk.FALSE)
        def showmessage():
            messagebox.showwarning('警告', '请不要关闭这个窗口...', parent=win)
        win.protocol('WM_DELETE_WINDOW', showmessage)
        f = font.Font(root=win, family='HarmonyOS Sans SC')
        f['size'] = 12
        mainframe = ttk.Frame(win, padding=5)
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)
        lab0 = ttk.Label(mainframe, text='正在检查更新...', font=f)
        lab0.grid(column=1, row=1, sticky=(tk.W, tk.N))
        tmp = window_interrupt(win, self._basket)
        tmp.start()
        win.mainloop()


class Window_login(threading.Thread):
    def __init__(self, picPath: str, e0:threading.Event, e1: threading.Event, e2:threading.Event, e3:threading.Event):
        super().__init__()
        self._picPath = picPath
        self._e0 = e0
        self._e1 = e1
        self._e2 = e2
        self._e3 = e3

    def run(self) -> None:
        basket = list()
        win = Window_login_window(self._picPath, basket, self._e3)
        win.start()
        time.sleep(0.2)
        while not basket[1]:
            time.sleep(0.2)
            if self._e2.is_set():
                basket[2].set('登录失败，请重新尝试...')
                time.sleep(1)
                break
            if self._e0.is_set() and not self._e1.is_set():
                basket[2].set('扫描成功，请确认...')
                continue
            if self._e1.is_set() or self._e3.is_set():
                break
        basket[0].destroy()


class Window_login_window(threading.Thread):
    def __init__(self, picPath: str, basket: list, e3: threading.Event):
        super().__init__()
        self._picPath = picPath
        self._basket = basket
        self._e3 = e3

    def run(self) -> None:
        win = tk.Tk()
        self._basket.append(win)
        self._basket.append(False)
        win.title('BiliDownloader-登录')
        win.geometry('+200+200')
        win.iconbitmap(os.path.join(programPath, 'src/icon.ico'))
        win.resizable(tk.FALSE, tk.FALSE)
        def showmessage():
            tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno')
            if tmp:
                self._e3.set()
                self._basket[1] = True
        win.protocol('WM_DELETE_WINDOW', showmessage)
        f = font.Font(root=win, family='HarmonyOS Sans SC')
        f['size'] = 11
        btnStyle = ttk.Style(win)
        btnStyle.configure('TButton', font=('HarmonyOS Sans SC', 11))
        mainframe = ttk.Frame(win)
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S))
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)
        pic0 = tk.PhotoImage(master=win, file=self._picPath)
        var0 = tk.StringVar(master=win)
        var0.set('请在 bilibili 手机客户端扫码登录...')
        self._basket.append(var0)
        lab0 = ttk.Label(mainframe, textvariable=var0, font=f)
        lab0.pack(side=tk.TOP)
        lab1 = ttk.Label(mainframe, image=pic0)
        lab1.pack(fill=tk.BOTH, side=tk.TOP)
        win.mainloop()


def window_setVar(PID_get, programPath_get):
    global PID
    global programPath
    PID = PID_get
    programPath = programPath_get


def window_main():
    print('Please Run As Module...')

if __name__ == '__main__':
    window_main()
