#include "framework.h"

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PWSTR pCmdLine, int nCmdShow)
{
	WinExec(".\\bin\\BiliDownloader.exe .\\src\\videoDownloaderWindow.pyc", SW_HIDE);
	return 0;
}
