#include <Windows.h>
#include <WinBase.h>

int WINAPI WinMain(
    HINSTANCE hInstance,
    HINSTANCE hPrevInstance,
    LPSTR lpCmdLine,
    int nShowCmd
)
{
    SHELLEXECUTEINFO sei = { sizeof(SHELLEXECUTEINFO) };
    sei.lpVerb = TEXT("runas");
    sei.lpFile = TEXT(".\\bin\\BiliDownloader.exe");
    sei.nShow = SW_SHOWNORMAL;
    ShellExecuteEx(&sei);
    //if (!ShellExecuteEx(&sei))
    //{
    //    DWORD dwStatus = GetLastError();
    //    if (dwStatus == ERROR_CANCELLED)
    //    {
    //        printf("提升权限被用户拒绝\n");
    //    }
    //    else if (dwStatus == ERROR_FILE_NOT_FOUND)
    //    {
    //        printf("所要执行的文件没有找到\n");
    //    }
    //}
    return 0;
}
