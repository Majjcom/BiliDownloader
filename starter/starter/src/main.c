#include <Windows.h>
#include <WinBase.h>

int WINAPI WinMain(
    _In_ HINSTANCE hInstance,
    _In_opt_ HINSTANCE hPrevInstance,
    _In_ LPSTR lpCmdLine,
    _In_ int nShowCmd
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
    //        printf("����Ȩ�ޱ��û��ܾ�\n");
    //    }
    //    else if (dwStatus == ERROR_FILE_NOT_FOUND)
    //    {
    //        printf("��Ҫִ�е��ļ�û���ҵ�\n");
    //    }
    //}
    return 0;
}
