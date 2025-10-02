@echo off
pyinstaller ^
-D ^
-n BiliDownloader ^
--distpath dist.pyinstaller/dist ^
--workpath dist.pyinstaller/build ^
-w ^
-i res\icon\icon.ico ^
--uac-admin ^
--additional-hooks-dir pyinstaller_config ^
main.py
