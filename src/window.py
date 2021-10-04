from tkinter import ttk, messagebox, font
import tkinter as tk
import threading
import time
import os

PID = os.getpid();

async def window_warn(text : str):
    win = tk.Tk();
    win.title('BiliDownloader');
    win.geometry('400x60+200+200');
    win.iconbitmap('../src/icon.ico');
    win.resizable(tk.TRUE, tk.FALSE);
    f = font.Font(root=win, name='TkTextFont', exists=True);
    f['size'] = 11;
    mainframe = ttk.Frame(win, padding=5);
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S));
    win.columnconfigure(0, weight=1);
    win.rowconfigure(0, weight=1);
    t0 = tk.Variable(win);
    t0.set(text);
    lab0 = ttk.Label(mainframe, textvariable=t0, font=f);
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W));
    def callback():
        win.destroy();
    btn0 = ttk.Button(mainframe, text='OK', command=callback);
    btn0.grid(column=1, row=2, sticky=(tk.W, tk.S));
    win.mainloop();
    return;


async def window_warn_big_2(text : str):
    win = tk.Tk();
    win.title('BiliDownloader');
    win.geometry('400x80+200+200');
    win.iconbitmap('../src/icon.ico');
    win.resizable(tk.FALSE, tk.FALSE);
    f = font.Font(root=win, name='TkTextFont', exists=True);
    f['size'] = 11;
    mainframe = ttk.Frame(win, padding=5);
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S));
    win.columnconfigure(0, weight=1);
    win.rowconfigure(0, weight=1);
    tmp = str();
    for i in range(len(text)):
        tmp += text[i];
        if (i + 1) % 28 == 0:
            tmp += '\n';
    t0 = tk.Variable(win);
    t0.set(tmp);
    lab0 = ttk.Label(mainframe, textvariable=t0, font=f);
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W));
    def callback():
        win.destroy();
    btn0 = ttk.Button(mainframe, text='OK', command=callback);
    btn0.grid(column=1, row=2, sticky=(tk.W, tk.S));
    win.mainloop();
    return;


async def window_ask() -> str:
    global retv;
    retv = 'a';
    win = tk.Tk();
    win.title('BiliDownloader');
    win.geometry('400x110+200+200');
    win.iconbitmap('../src/icon.ico');
    win.resizable(tk.FALSE, tk.FALSE);
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno');
        if tmp:
            global PID;
            os.kill(PID, 15);
    win.protocol('WM_DELETE_WINDOW', showmessage);
    f = font.Font(root=win, name='TkTextFont', exists=True);
    f['size'] = 11;
    mainframe = ttk.Frame(win, padding=5);
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S));
    win.columnconfigure(0, weight=1);
    win.rowconfigure(0, weight=1);
    lab0 = ttk.Label(mainframe, text='请输入视频的BV号、AV号或MD号\n(包含开头的BV、AV和MD):', font=f);
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W));
    text = tk.Variable(win);
    etr0 = ttk.Entry(mainframe, width=30, textvariable=text);
    etr0.grid(column=1, row=2, sticky=(tk.N, tk.W));
    def callback():
        global retv;
        retv = text.get().replace(' ', '');
        win.destroy();
    btn0 = ttk.Button(mainframe, text='OK', command=callback);
    btn0.grid(column=2, row=3, sticky=(tk.E, tk.S));
    win.mainloop();
    return retv;


async def window_showupdate():
    win = tk.Tk();
    win.title('BiliDownloader');
    win.geometry('400x80+200+200');
    win.iconbitmap('../src/icon.ico');
    win.resizable(tk.TRUE, tk.FALSE);
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno');
        if tmp:
            win.destroy();
    win.protocol('WM_DELETE_WINDOW', showmessage);
    f = font.Font(root=win, name='TkTextFont', exists=True);
    f['size'] = 11;
    mainframe = ttk.Frame(win, padding=5);
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S));
    win.columnconfigure(0, weight=1);
    win.rowconfigure(0, weight=1);
    lab0 = ttk.Label(mainframe, text='有新的版本更新，即将开始下载\nP.S. 本软件正处于开发阶段，更新频繁，请见谅，每次更新都将会有稳定性的提升', font=f);
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W));
    def callback():
        win.destroy();
    btn0 = ttk.Button(mainframe, text='OK', command=callback);
    btn0.grid(column=1, row=2, sticky=(tk.S, tk.W));
    win.mainloop();
    return;


async def window_confirm(text : str):
    global retv;
    retv = False;
    win = tk.Tk();
    win.title('BiliDownloader');
    win.geometry('400x150+200+200');
    win.iconbitmap('../src/icon.ico');
    win.resizable(tk.FALSE, tk.FALSE);
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno');
        if tmp:
            global PID;
            os.kill(PID, 15);
    win.protocol('WM_DELETE_WINDOW', showmessage);
    f = font.Font(root=win, name='TkTextFont', exists=True);
    f['size'] = 11;
    mainframe = ttk.Frame(win, padding=5);
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.S, tk.W));
    win.columnconfigure(0, weight=1);
    win.rowconfigure(0, weight=1);
    t = tk.Variable(win);
    t.set(text);
    lab0 = ttk.Label(mainframe, textvariable=t, font=f);
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W));
    def callback0():
        global retv
        retv = True;
        win.destroy();
    def callback1():
        win.destroy();
    btn0 = ttk.Button(mainframe, text='YES', command=callback0);
    btn0.grid(column=1, row=2, sticky=(tk.W));
    btn1 = ttk.Button(mainframe, text='NO', command=callback1);
    btn1.grid(column=1, row=3, sticky=(tk.W));
    win.mainloop();
    return retv;


async def window_config_p(text : str):
    global retv;
    retv = '';
    win = tk.Tk();
    win.title('BiliDownloader');
    win.geometry('400x110+200+200');
    win.iconbitmap('../src/icon.ico');
    win.resizable(tk.FALSE, tk.FALSE);
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno');
        if tmp:
            global PID;
            os.kill(PID, 15);
    win.protocol('WM_DELETE_WINDOW', showmessage);
    f = font.Font(root=win, name='TkTextFont', exists=True);
    f['size'] = 11;
    mainframe = ttk.Frame(win, padding=5);
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.S, tk.W));
    win.columnconfigure(0, weight=1);
    win.rowconfigure(0, weight=1);
    t0 = tk.Variable(win)
    t0.set(text);
    lab0 = ttk.Label(mainframe, textvariable=t0, font=f);
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W));
    lab1 = ttk.Label(mainframe, text='请选择下载范围, 用","分隔(如1-1或1-5或1-1, 3-5): ', font=f);
    lab1.grid(column=1, row=2, sticky=(tk.W));
    t1 = tk.Variable(win);
    etr0 = ttk.Entry(mainframe, textvariable=t1);
    etr0.grid(column=1, row=3, sticky=(tk.W));
    def callback():
        global retv;
        retv = t1.get();
        win.destroy();
    btn0 = ttk.Button(mainframe, text='OK', command=callback);
    btn0.grid(column=1, row=4, sticky=(tk.W, tk.S));
    win.mainloop();
    return retv;


async def window_config_q(tip : str):
    global retv;
    retv = '';
    win = tk.Tk();
    win.title('BiliDownloader');
    win.geometry('400x120+200+200');
    win.iconbitmap('../src/icon.ico');
    win.resizable(tk.FALSE, tk.FALSE);
    def showmessage():
        tmp = messagebox.askyesno(title='确认', message='确认关闭?', parent=win, type='yesno');
        if tmp:
            global PID;
            os.kill(PID, 15);
    def showHelp():
        messagebox.showinfo(title='提示',
                            parent=win,
                            message='提示:\n\n'
                                    '120\t4K\n116\t1080p60\n112\t1080p+\n80\t1080p\n72\t720p60\n64\t720p\n32\t480p\n16\t320p\n\n'
                                    '如果出现一直无法下载的情况可以稍微降低清晰度哦ლ(´ڡ`ლ)\n\n'
                                    'P.S.现已支持4k分辨率视频下载!!!');
    win.protocol('WM_DELETE_WINDOW', showmessage);
    f = font.Font(root=win, name='TkTextFont', exists=True);
    f['size'] = 11;
    mainframe = ttk.Frame(win, padding=5);
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S));
    win.columnconfigure(0, weight=1);
    win.rowconfigure(0, weight=1);
    lab0 = ttk.Label(mainframe, text='请选择清晰度(可选: {}): '.format(tip), font=f);
    lab0.grid(column=1, row=1, stick=(tk.N, tk.W));
    t0 = tk.Variable(win);
    t0.set(tip.split(', ', 1)[0]);
    etr0 = ttk.Entry(mainframe, textvariable=t0, width=10);
    etr0.grid(column=1, row=2, sticky=(tk.W));
    def callback():
        global retv;
        retv = t0.get();
        win.destroy();
    btn0 = ttk.Button(mainframe, text='OK', command=callback);
    btn0.grid(column=1, row=3, sticky=(tk.W));
    btn1 = ttk.Button(mainframe, text='提示', command=showHelp);
    btn1.grid(column=1, row=4, sticky=(tk.W));
    win.mainloop();
    return retv;


async def window_finish(text):
    win = tk.Tk();
    win.title('BiliDownloader');
    win.geometry('400x90+200+200');
    win.iconbitmap('../src/icon.ico');
    win.resizable(tk.FALSE, tk.FALSE);
    f = font.Font(root=win, name='TkTextFont', exists=True);
    f['size'] = 11;
    mainframe = ttk.Frame(win, padding=5);
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S));
    win.columnconfigure(0, weight=1);
    win.rowconfigure(0, weight=1);
    lab0 = ttk.Label(mainframe, text='视频全部下载完成，保存在: ', font=f);
    lab0.grid(column=1, row=1, sticky=(tk.N, tk.W));
    t0 = tk.Variable(win);
    t0.set(text);
    etr0 = ttk.Entry(mainframe, textvariable=t0, state='readonly', width=30);
    etr0.grid(column=1, row=2, sticky=(tk.W));
    def callback():
        win.destroy();
    btn0 = ttk.Button(mainframe, text='OK', command=callback);
    btn0.grid(column=1, row=3, sticky=(tk.S, tk.W));
    win.mainloop();
    return;


class window_interrupt(threading.Thread):
    def __init__(self, this : tk.Tk, v):
        threading.Thread.__init__(self);
        self._this = this;
        self._v = v;

    def run(self):
        while True:
            time.sleep(0.1);
            if self._v[0]:
                time.sleep(0.5);
                self._this.destroy();
                return;

class window_geturl(threading.Thread):
    def __init__(self, v):
        threading.Thread.__init__(self);
        self._v = v; # 0: isRun, 1: t0

    def run(self) -> None:
        win = tk.Tk();
        win.title('BiliDownloader');
        win.geometry('400x35+200+200');
        win.iconbitmap('../src/icon.ico');
        win.resizable(tk.FALSE, tk.FALSE);
        def showmessage():
            messagebox.showwarning('警告', '请不要关闭这个窗口...', parent=win);
        win.protocol('WM_DELETE_WINDOW', showmessage);
        f = font.Font(root=win, name='TkTextFont', exists=True);
        f['size'] = 11;
        mainframe = ttk.Frame(win, padding=5);
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S));
        win.columnconfigure(0, weight=1);
        win.rowconfigure(0, weight=1);
        t0 = tk.Variable(win);
        t0.set('null');
        self._v.append(t0);
        lab0 = ttk.Label(mainframe, textvariable=t0, font=f);
        lab0.grid(column=1, row=1, sticky=(tk.N, tk.W));
        tmp = window_interrupt(win, self._v);
        tmp.start();
        win.mainloop();
        return;


class window_downloas(threading.Thread):
    def __init__(self, v):
        threading.Thread.__init__(self);
        self._v = v; # 0: isRun, 1: t0, 2: t1, 3: t2, 4: t3, 5: bar

    def run(self) -> None:
        win = tk.Tk();
        win.title('BiliDownloader');
        win.geometry('400x110+200+200');
        win.iconbitmap('../src/icon.ico');
        win.resizable(tk.FALSE, tk.FALSE);
        def showmessage():
            messagebox.showwarning('警告', '请不要关闭这个窗口...', parent=win);
        win.protocol('WM_DELETE_WINDOW', showmessage);
        f = font.Font(root=win, name='TkTextFont', exists=True);
        f['size'] = 11;
        mainframe = ttk.Frame(win, padding=5);
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S));
        win.columnconfigure(0, weight=1);
        win.rowconfigure(0, weight=1);
        t0 = tk.Variable(win);
        t0.set('null');
        self._v.append(t0);
        lab0 = ttk.Label(mainframe, textvariable=t0, font=f);
        lab0.grid(column=1, row=1, sticky=(tk.N, tk.W));
        t1 = tk.Variable(win)
        t1.set('null');
        self._v.append(t1);
        lab1 = ttk.Label(mainframe, textvariable=t1, font=f);
        lab1.grid(column=1, row=2, sticky=(tk.W));
        t2 = tk.Variable(win);
        t2.set('null')
        self._v.append(t2);
        lab2 = ttk.Label(mainframe, textvariable=t2, font=f);
        lab2.grid(column=1, row=3, sticky=(tk.W));
        t3 = tk.Variable(win);
        t3.set(0.0);
        self._v.append(t3);
        bar0 = ttk.Progressbar(
                mainframe,
                orient=tk.HORIZONTAL,
                length=250,
                mode='determinate',
                variable=t3
            );
        bar0.grid(column=1, row=4, sticky=(tk.S, tk.W));
        self._v.append(bar0);
        tmp = window_interrupt(win, self._v);
        tmp.start();
        win.mainloop();
        return;


class window_updating(threading.Thread):
    def __init__(self, arg : list):
        threading.Thread.__init__(self);
        self._arg = arg;

    def run(self):
        global f;
        win = tk.Tk();
        win.title('BiliDownloader Update');
        win.geometry('400x60+200+200');
        win.iconbitmap('../src/icon.ico');
        win.resizable(tk.FALSE, tk.FALSE);
        def showmessage():
            messagebox.showwarning('警告', '请不要关闭这个窗口...', parent=win);
        win.protocol('WM_DELETE_WINDOW', showmessage);
        f = font.Font(root=win, name='TkTextFont', exists=True);
        f['size'] = 11;
        mainframe = ttk.Frame(win, padding=5);
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.W, tk.S));
        win.columnconfigure(0, weight=1);
        win.rowconfigure(0, weight=1);
        lab0 = ttk.Label(mainframe, text='正在下载更新...', font=f);
        lab0.grid(column=1, row=1, sticky=(tk.W, tk.N));
        t0 = tk.Variable(win);
        t0.set(0.0);
        self._arg.append(t0);
        bar0 = ttk.Progressbar(
            mainframe,
            orient=tk.HORIZONTAL,
            length=250,
            mode='determinate',
            variable=t0
        );
        bar0.grid(column=1, row=2, sticky=(tk.W, tk.S));
        tmp = window_interrupt(win, self._arg);
        tmp.start();
        win.mainloop();

def window_main():
    print('Please Run As Module...');

if __name__ == '__main__':
    window_main();
