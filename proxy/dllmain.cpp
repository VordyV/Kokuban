#define FMT_UNICODE 0

#include <format>
#include <string>
#include <windows.h>
#include "MinHook/include/MinHook.h"

const std::string VERSION = "1.0";
const std::string TITLE = "amanda";
const std::string LIBRARY = "kbuf.dll"; 

typedef void (*OnStart_t)();
typedef void (*OnStop_t)();
typedef VOID (WINAPI* ExitProcess_t)(UINT);

static bool shouldExit = false;
static ExitProcess_t OriginalExitProcess = nullptr;
static HANDLE thread_Main = nullptr; 

void Print(std::string value)
{
    std::string text = "[" + TITLE + "] " + value + "\n";
    OutputDebugStringA(text.c_str());
}

VOID WINAPI HookExitProcess(UINT exitCode)
{
    Print("shutdown...");
    
    shouldExit = true;
    if (thread_Main) WaitForSingleObject(thread_Main, 3000);
    CloseHandle(thread_Main);
    thread_Main = nullptr;
    
    OriginalExitProcess(exitCode);
}

DWORD WINAPI MainThread(LPVOID lpParam) {
    MH_Initialize();

    MH_CreateHook(
        &ExitProcess,
        &HookExitProcess,
        reinterpret_cast<void**>(&OriginalExitProcess));

    MH_EnableHook(&ExitProcess);
    
    HMODULE library = LoadLibraryA(LIBRARY.c_str());
    if (library == NULL) Print("failed to load " + LIBRARY);
    
    OnStart_t OnStart = (OnStart_t)GetProcAddress(library, "OnStart");
    if (OnStart) OnStart();

    while (!shouldExit)
    {
        
    }
    
    OnStop_t OnStop = (OnStop_t)GetProcAddress(library, "OnStop");
    if (OnStop) OnStop();
                
    FreeLibrary(library);
    
    Print("stop");
    return 0;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved)
{
    switch (ul_reason_for_call)
    {
        case DLL_PROCESS_ATTACH:
            {
                Print("start v" + VERSION);
                //Print(fmt::format("start v{}", VERSION));
                thread_Main = CreateThread(nullptr, 0, MainThread, nullptr, 0, nullptr);
                break;
            }
        case DLL_THREAD_ATTACH:
            {
                break;
            }
        case DLL_THREAD_DETACH:
            {
                break;
            }
        case DLL_PROCESS_DETACH:
            {
                shouldExit = true;
                break;
            }
    }
	
    return TRUE;
}

extern "C" int __cdecl deinitDll() {
    return 0;
}

extern "C" bool __cdecl initDll(int a1) {
    return true;
}
