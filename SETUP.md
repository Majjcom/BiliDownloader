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
将`icon`目录下的`icon.ico`复制到`src`中

### 运行
在`src/../`目录中使用以下命令
```shell
python ./src/main.py
```
当然，也可以写 shell 文件来快速启动，这里不再讲解，参照此处的 shell 即可

## 2.构建 Windows 安装包

***文档编写中...***
