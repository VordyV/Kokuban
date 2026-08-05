#pragma once
#include <d3d9.h>
#include <Windows.h>
#include <functional>
#include <string>
#include "debug.h"
#include "ImGui/imgui.h"
#include "MinHook/include/MinHook.h"
#include "Imgui/imgui_internal.h"

extern LRESULT ImGui_ImplWin32_WndProcHandler(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

enum DialogType
{
    Info,
};

struct ImFont;

class Graphics
{
public:
    static HWND window;
    static std::function<void(bool)> onShutdown;
    static std::function<void(bool)> onResetInvalidateDeviceObjects;
    static std::function<void(bool)> onResetCreateDeviceObjects;
    static std::function<void(bool)> onEndScene;
    static std::function<void(bool, LPDIRECT3DDEVICE9, HWND)> onInitImgui;
    static std::function<void(bool)> onShutdownImgui;
    static std::function<void(bool, LPDIRECT3DDEVICE9)> onBeginImgui;
    static std::function<IMGUI_IMPL_API LRESULT(bool, HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam)> onWndProcImplWin32;
    static std::function<void(WPARAM)> onKeyPress;

    static void Init();
    static void ReleaseAll();
    static void setWindow(HWND value);

private:
    using EndScene_t = HRESULT(WINAPI*)(LPDIRECT3DDEVICE9);
    using Reset_t = HRESULT(WINAPI*)(LPDIRECT3DDEVICE9, D3DPRESENT_PARAMETERS*);
    
    static bool imgui_init;
    static WNDPROC O_WndProc;
    static EndScene_t O_EndScene;
    static Reset_t O_Reset;

    static HRESULT WINAPI HookReset(LPDIRECT3DDEVICE9 device, D3DPRESENT_PARAMETERS* params);
    static HRESULT WINAPI HookEndScene(LPDIRECT3DDEVICE9 device);
    static void InitImGui(LPDIRECT3DDEVICE9 device);
    static LRESULT WINAPI WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);
    static void ShutdownImGui();
    static void ShutdownHooks();
    static BOOL CALLBACK EnumWindowsProc(HWND hwnd, LPARAM lParam);
    static HWND FindMainWindow();
};