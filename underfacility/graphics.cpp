#include "Graphics.h"
#include <d3d9.h>
#include <functional>
#include <iostream>

HWND Graphics::window = nullptr;
std::function<void(bool)> Graphics::onShutdown = nullptr;
std::function<void(bool)> Graphics::onResetInvalidateDeviceObjects = nullptr;
std::function<void(bool)> Graphics::onResetCreateDeviceObjects = nullptr;
std::function<void(bool)> Graphics::onEndScene = nullptr;
std::function<void(bool, LPDIRECT3DDEVICE9, HWND)> Graphics::onInitImgui = nullptr;
std::function<void(bool)> Graphics::onShutdownImgui = nullptr;
std::function<void(bool, LPDIRECT3DDEVICE9)> Graphics::onBeginImgui = nullptr;
std::function<IMGUI_IMPL_API LRESULT(bool, HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam)> Graphics::onWndProcImplWin32 = nullptr;
std::function<void(WPARAM)> Graphics::onKeyPress = nullptr;

bool Graphics::imgui_init = false;
WNDPROC Graphics::O_WndProc = nullptr;
Graphics::EndScene_t Graphics::O_EndScene = nullptr;
Graphics::Reset_t Graphics::O_Reset = nullptr;

void Graphics::Init()
{
    window = Graphics::FindMainWindow();

    WNDCLASSEX wc{};
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = DefWindowProc;
    wc.hInstance = GetModuleHandleW(nullptr);
    wc.lpszClassName = L"DummyD3D9Window";

    RegisterClassExW(&wc);

    HWND hwnd = CreateWindowW(
        wc.lpszClassName,
        wc.lpszClassName,
        WS_OVERLAPPEDWINDOW,
        0, 0, 100, 100,
        nullptr, nullptr,
        wc.hInstance,
        nullptr
    );

    if (!hwnd)
        return;

    IDirect3D9* d3d = Direct3DCreate9(D3D_SDK_VERSION);
    if (!d3d)
    {
        DestroyWindow(hwnd);
        UnregisterClassW(wc.lpszClassName, wc.hInstance);
        return;
    }

    D3DPRESENT_PARAMETERS pp{};
    pp.Windowed = TRUE;
    pp.SwapEffect = D3DSWAPEFFECT_DISCARD;
    pp.hDeviceWindow = hwnd;

    IDirect3DDevice9* device = nullptr;
    if (SUCCEEDED(d3d->CreateDevice(
        D3DADAPTER_DEFAULT,
        D3DDEVTYPE_HAL,
        hwnd,
        D3DCREATE_SOFTWARE_VERTEXPROCESSING,
        &pp,
        &device)))
    {
        void** vtable = *reinterpret_cast<void***>(device);

        MH_Initialize();
        MH_CreateHook(vtable[16], &HookReset, reinterpret_cast<void**>(&Graphics::O_Reset));
        MH_CreateHook(vtable[42], &HookEndScene, reinterpret_cast<void**>(&Graphics::O_EndScene));
        MH_EnableHook(MH_ALL_HOOKS);

        device->Release();
    }

    d3d->Release();
    DestroyWindow(hwnd);
    UnregisterClassW(wc.lpszClassName, wc.hInstance);
}

void Graphics::ReleaseAll()
{
    ShutdownHooks();
    ShutdownImGui();
}

void Graphics::setWindow(HWND value)
{
    Graphics::window = value;
}

HRESULT WINAPI Graphics::HookReset(LPDIRECT3DDEVICE9 device, D3DPRESENT_PARAMETERS* params)
{
    if (Graphics::imgui_init)
        Graphics::onResetInvalidateDeviceObjects(Graphics::imgui_init);
        //ImGui_ImplDX9_InvalidateDeviceObjects(); <!>

    HRESULT hr = Graphics::O_Reset(device, params);

    if (Graphics::imgui_init)
        Graphics::onResetCreateDeviceObjects(Graphics::imgui_init);
        //ImGui_ImplDX9_CreateDeviceObjects(); <!>

    return hr;
}

HRESULT WINAPI Graphics::HookEndScene(LPDIRECT3DDEVICE9 device)
{
    if (!Graphics::imgui_init)
    {
        Graphics::InitImGui(device);
        Graphics::imgui_init = true;
        Graphics::onBeginImgui(Graphics::imgui_init, device); //<!>

        Graphics::O_WndProc = reinterpret_cast<WNDPROC>(
            SetWindowLongPtr(window, GWLP_WNDPROC, reinterpret_cast<LONG_PTR>(Graphics::WndProc))
        );
    }
    
    Graphics::onEndScene(Graphics::imgui_init);

    return Graphics::O_EndScene(device);
}

void Graphics::InitImGui(LPDIRECT3DDEVICE9 device)
{
    /*ImGui::CreateContext();

    ImGuiIO& io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NoMouseCursorChange;
    io.MouseDrawCursor = false;
    io.IniFilename = nullptr;
    io.LogFilename = nullptr;

    ImGui::StyleColorsDark();

    ImFontConfig fontConfig{};
    fontConfig.OversampleH = 3;
    fontConfig.OversampleV = 3;
    fontConfig.PixelSnapH = true;

    ImGui_ImplWin32_Init(Graphics::window);
    ImGui_ImplDX9_Init(device);*/
    // <!>
    Graphics::onInitImgui(Graphics::imgui_init, device, Graphics::window);
}

LRESULT WINAPI Graphics::WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    
    if (Graphics::imgui_init && Graphics::onWndProcImplWin32(Graphics::imgui_init, hWnd, msg, wParam, lParam)) //<!>
        return TRUE;

    if (msg == WM_DESTROY || msg == WM_CLOSE)
    {
        //if (onShutdown)
        //    onShutdown();
    }
    
    if (msg == WM_KEYDOWN) {
        Graphics::onKeyPress(wParam);
    }

    return CallWindowProc(Graphics::O_WndProc, hWnd, msg, wParam, lParam);
}

void Graphics::ShutdownImGui()
{
    if (!Graphics::imgui_init)
        return;

    if (Graphics::window && Graphics::O_WndProc)
        SetWindowLongPtr(Graphics::window, GWLP_WNDPROC, reinterpret_cast<LONG_PTR>(Graphics::O_WndProc));

    //ImGui_ImplDX9_Shutdown();
    //ImGui_ImplWin32_Shutdown();
    //ImGui::DestroyContext(); <!>
    Graphics::onShutdownImgui(Graphics::imgui_init);

    Graphics::imgui_init = false;
}

void Graphics::ShutdownHooks()
{
    MH_DisableHook(MH_ALL_HOOKS);
    MH_Uninitialize();
}

BOOL CALLBACK Graphics::EnumWindowsProc(HWND hwnd, LPARAM lParam)
{
    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);

    if (pid != GetCurrentProcessId())
        return TRUE;

    if (!IsWindowVisible(hwnd))
        return TRUE;

    if (GetWindow(hwnd, GW_OWNER) != nullptr)
        return TRUE;

    *reinterpret_cast<HWND*>(lParam) = hwnd;
    return FALSE;
}

HWND Graphics::FindMainWindow()
{
    HWND hwnd = nullptr;
    EnumWindows(EnumWindowsProc, reinterpret_cast<LPARAM>(&hwnd));
    return hwnd;
}