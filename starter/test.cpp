#include <windows.h>

int main ()
{
	HWND hwnd;
    hwnd=FindWindow("ConsoleWindowClass",NULL); //处理顶级窗口的类名和窗口名称匹配指定的字符串,不搜索子窗口。
    if(hwnd)
    {
        ShowWindow(hwnd,SW_HIDE);               //设置指定窗口的显示状态
    }
	
	WinExec(".\\Lib\\BiliDownloader.exe .\\src\\videoDownloaderWindow.py", SW_HIDE);
	return 0;
}