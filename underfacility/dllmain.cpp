#include <windows.h>
#include "debug.h"
#include "graphics.h"

//extern LRESULT ImGui_ImplWin32_WndProcHandler(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

typedef void (*OnStart_t)();
typedef void (*OnStop_t)();
typedef void (*OnResetInvalidateDeviceObjects_t)(int);
typedef void (*OnResetCreateDeviceObjects_t)(int);
typedef void (*OnInitImgui_t)(int, void*, void*);
typedef void (*OnShutdownImgui_t)(int);
typedef LRESULT (*OnWndProcImplWin32_t)(int, void*, unsigned int, uintptr_t, intptr_t);
typedef void (*OnBeginImgui_t)(int, void*);
typedef void (*OnEndScene_t)(int);
typedef void (*OnKeyPress_t)(uintptr_t);

#pragma comment(lib, "d3d9.lib")

static bool shouldExit = false;
static HANDLE thread_UI = nullptr;

DWORD WINAPI ThreadUI(LPVOID lpParameter)
{
    HMODULE library = LoadLibraryA(LIBRARY.c_str());
    if (library == NULL)
    {
        Print("failed to load " + LIBRARY);
        return 1;
    }
    
    OnStart_t OnStart = (OnStart_t)GetProcAddress(library, "OnStart");
    if (OnStart) OnStart();
    
    OnResetInvalidateDeviceObjects_t OnResetInvalidateDeviceObjects = (OnResetInvalidateDeviceObjects_t)GetProcAddress(library, "OnResetInvalidateDeviceObjects");
    OnResetCreateDeviceObjects_t OnResetCreateDeviceObjects = (OnResetCreateDeviceObjects_t)GetProcAddress(library, "OnResetCreateDeviceObjects");
    OnInitImgui_t OnInitImgui = (OnInitImgui_t)GetProcAddress(library, "OnInitImgui");
    OnShutdownImgui_t OnShutdownImgui = (OnShutdownImgui_t)GetProcAddress(library, "OnShutdownImgui");
    OnWndProcImplWin32_t OnWndProcImplWin32 = (OnWndProcImplWin32_t)GetProcAddress(library, "OnWndProcImplWin32");
    OnBeginImgui_t OnBeginImgui = (OnBeginImgui_t)GetProcAddress(library, "OnBeginImgui");
    OnEndScene_t OnEndScene = (OnEndScene_t)GetProcAddress(library, "OnEndScene");
    OnKeyPress_t OnKeyPress = (OnKeyPress_t)GetProcAddress(library, "OnKeyPress");
    
    Graphics::Init();
    Graphics::onResetInvalidateDeviceObjects = [&OnResetInvalidateDeviceObjects](int init_imgui)
    {
        if (OnResetInvalidateDeviceObjects) OnResetInvalidateDeviceObjects(init_imgui);
    };
    Graphics::onResetCreateDeviceObjects = [&OnResetCreateDeviceObjects](int init_imgui)
    {
        if (OnResetCreateDeviceObjects) OnResetCreateDeviceObjects(init_imgui);
    };
    Graphics::onInitImgui = [&OnInitImgui](int init_imgui, LPDIRECT3DDEVICE9 device, HWND window)
    {
        if (OnInitImgui) OnInitImgui(init_imgui, device, window);
    };
    Graphics::onShutdownImgui = [&OnShutdownImgui](int init_imgui)
    {
        if (OnShutdownImgui) OnShutdownImgui(init_imgui);
    };
    Graphics::onWndProcImplWin32 = [&OnWndProcImplWin32](int init_imgui, void* hWnd, unsigned int msg, uintptr_t wParam, intptr_t lParam)
    {
        //if (OnResetInvalidateDeviceObjects)
        if (!OnWndProcImplWin32) return 0L;
        LRESULT result = OnWndProcImplWin32(init_imgui, hWnd, msg, wParam, lParam);
        return result;
    };
    Graphics::onBeginImgui = [&OnBeginImgui](int init_imgui, LPDIRECT3DDEVICE9 device)
    {
        if (OnBeginImgui) OnBeginImgui(init_imgui, device);
    };
    Graphics::onEndScene = [&OnEndScene](int init_imgui)
    {
        if (OnEndScene) OnEndScene(init_imgui);
    };
    
    Graphics::onKeyPress = [&OnKeyPress](uintptr_t init_imgui)
    {
        if (OnKeyPress) OnKeyPress(init_imgui);
    };
    
    while (!shouldExit)
    {
        Sleep(100);
    }
    
    Graphics::ReleaseAll();
    
    OnStop_t OnStop = (OnStop_t)GetProcAddress(library, "OnStop");
    if (OnStop) OnStop();
                
    FreeLibrary(library);
    
    return 0;
}

extern "C" __declspec(dllexport)
void OnStart()
{
    thread_UI = CreateThread(NULL, 0, ThreadUI, NULL, 0, NULL);
    Print("start");
}

extern "C" __declspec(dllexport)
void OnStop()
{
    shouldExit = true;
    if (thread_UI) WaitForSingleObject(thread_UI, 3000);
    CloseHandle(thread_UI);
    thread_UI = nullptr;
    Print("stop");
}

/*BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved)
{
    switch (ul_reason_for_call)
    {
        case DLL_PROCESS_ATTACH:
            {
                
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
                
                break;
            }
    }
    return TRUE;
}*/