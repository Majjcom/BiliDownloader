# BiliDownloader 构建指南

## 1.直接运行py文件

### 准备运行环境
Python Version >= 3.10

Operating System >= Windows 10

### 快速安装依赖库
下载代码
```shell
git clone https://gitee.com/majjcom/bili-downloader.git
```
这里建议建立虚拟环境
```shell
python3 -m venv ./venv

# 激活虚拟环境，每次使用都需要运行这个
# 为了方便可以不使用虚拟环境
./venv/Scripts/activate
```

```shell
pip install -r requirements.txt
```

Windows 需要安装额外的库才能运行：

```shell
# 安装Windows依赖
pip install -r requirements_win.txt
```



### 运行前准备
下载支持AV1的[ffmpeg](https://majjcom.lanzouo.com/b01xc9emh)可执行文件，并将`ffmpeg.exe`解压至`src`同级目录的`ffmpeg`目录下（此目录可能需要自己创建）

链接密码：5ytb

目录结构大概是这样：

```
/--src/--main.py
 |     |-requirments.txt
 |-ffmpeg/--ffmpeg.exe
 |-...
```

仓库隐藏了服务密钥，可以使用离线模式，修改如下：

添加`const.py`到`src/Lib/bd_client`下，并添加以下内容：
```python
CONST_KEY=""
```

修改`src/update.py`，将`NO_UPDATE`设置为True



### 运行
在主目录下运行以下命令
```shell
cd src
python compile_ui.py
cd ..
pythonw src/main.py
```
当然，也可以写 shell 文件来快速启动，这里不再讲解，参照此处的 shell 即可



## 2. Linux构建独立可执行文件

### 构建环境准备

先根据上文准备好基本的运行环境。

再安装nuitka构建工具：

```shell
python -m pip install -U pip
pip install nuitka
```



### 构建

构建可能需要`patchelf`的包，请自行安装

```shell
cd src
python compile_ui.py
chmod +x ./build_nuitka_linux.sh
./build_nuitka_linux.sh
```

构建将输出在`dist.nuitka.linux`目录下

## 3. CLI

命令行工具复用 GUI 的下载线程，不需要启动窗口：

```shell
python -m pip install -e .
bili info BVxxxxxxxxxx
bili formats BVxxxxxxxxxx --page 1
bili download BVxxxxxxxxxx --output ./downloads --page all

# 不安装项目时，也可以直接运行脚本
python src/bili_cli.py info BVxxxxxxxxxx
```

CLI 默认复用 GUI 的 `data/userdata.json` 下载目录、编码、音频、弹幕和登录设置；也可以设置 `BILI_COOKIE` 或传入 `--cookie-file` 临时覆盖。FFmpeg 可通过 `--ffmpeg` 或 `BILI_FFMPEG` 指定。

从其他目录调用时，可以用 `--config-dir` 指向 GUI 的工作目录；命令行布尔选项支持对应的 `--no-*` 形式覆盖 GUI 设置。
