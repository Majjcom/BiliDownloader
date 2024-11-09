python -m nuitka \
--enable-plugins=pyside6 \
--standalone \
--user-package-configuration-file=nuitka_config/bili_api.nuitka-package.config.yaml \
--output-dir=../dist.nuitka.linux \
--deployment \
--output-filename=BiliDownloader \
main.py

MAIN_DIR=$HOME/.bili_downloader/
echo Creating MAIN_DIR $MAIN_DIR
mkdir $MAIN_DIR
echo Copying Files ...
cp ../CHANGELOG.md $MAIN_DIR
cp ../LICENSE $MAIN_DIR
cp -r ../ffmpeg $MAIN_DIR
echo Build Finished ...
