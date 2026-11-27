@echo off
python -m nuitka ^
--enable-plugins=pyside6 ^
--standalone ^
--windows-console-mode=hide ^
--user-package-configuration-file=nuitka_config/bili_api.nuitka-package.config.yaml ^
--output-dir=dist.portable.nuitka ^
--output-filename=BiliDownloader.exe ^
--company-name=Majjcom ^
--product-name=BiliDownloader ^
--file-version=%~1 ^
--product-version=%~1 ^
--copyright="Copyright (c) 2021-2026 Majjcom" ^
--windows-icon-from-ico="res/icon/icon.ico" ^
--show-progress ^
--deployment ^
--jobs=16 ^
main.py
