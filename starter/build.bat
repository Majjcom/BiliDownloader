@echo off
set LOCAL_PATH=%~dp0
set /p TCC_PATH=<tccpath.txt
set /p GCC_PATH=<gccpath.txt

if exist "%LOCAL_PATH%build" (
    rmdir /s /q "%LOCAL_PATH%build"
)
mkdir %LOCAL_PATH%build

echo compiling main.c
%TCC_PATH%\tcc -c main.c -o %LOCAL_PATH%build\main.o -Wall
echo compiling starter.rc
%GCC_PATH%\windres -i starter.rc -o %LOCAL_PATH%build\res.o
echo linking BiliDownloader.exe
%TCC_PATH%\tcc %LOCAL_PATH%build\main.o %LOCAL_PATH%build\res.o -o %LOCAL_PATH%build\BiliDownloader.exe -lshell32
echo build finished!
