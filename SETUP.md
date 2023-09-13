# BiliDownloader 构建指南

## 1.直接运行py文件

### 准备运行环境
Python Version >= 3.8.10

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
### 运行前准备
下载支持AV1的[ffmpeg](https://majjcom.lanzouy.com/iX5kY18c1dhi)可执行文件，并将`ffmpeg`文件夹解压至`main.py`所在的目录下

目录结构大概是这样：

```
/--main.py
 |-requirments.txt
 |-ffmpeg/--ffmpeg.exe
 |        |-xxx.dll
 |        |-...
 |-...
```



### 运行
在`src/../`目录中使用以下命令
```shell
python ./src/main.py
```
当然，也可以写 shell 文件来快速启动，这里不再讲解，参照此处的 shell 即可

## 2.构建 Windows 安装包

***文档编写中...***
