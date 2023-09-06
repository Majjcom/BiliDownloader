
#include <Windows.h>
#include <WinBase.h>

int WINAPI WinMain(
    _In_ HINSTANCE hInstance,
    _In_opt_ HINSTANCE hPrevInstance,
    _In_ LPSTR lpCmdLine,
    _In_ int nShowCmd
)
{
	::WinExec(".\\bin\\BiliDownloader.exe", SW_SHOW);
	return 0;
}
