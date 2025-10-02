@echo off
pyinstaller ^
-D ^
-n BiliDownloader ^
--distpath dist.pyinstaller.test/dist ^
--workpath dist.pyinstaller.test/build ^
-c ^
-i res\icon\icon.ico ^
--uac-admin ^
--additional-hooks-dir pyinstaller_config ^
main.py
