@echo off
pyinstaller ^
-D ^
-n BiliDownloader ^
--distpath dist.pyinstaller/dist ^
--workpath dist.pyinstaller/build ^
-w ^
-i res\icon\icon.ico ^
--additional-hooks-dir pyinstaller_config ^
main.py
