using System.Collections;
using System.Net;
using System.Numerics;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using Hexa.NET.ImGui;
using Hexa.NET.ImGui.Backends.D3D9;
using Hexa.NET.ImGui.Backends.Win32;
using Microsoft.Win32;
using P = speaker.Phrases;
using Timer = System.Timers.Timer;

namespace speaker;

public enum DialogType
{
    Ban = 0,
    Kick = 1,
    Other = 2
}

public static unsafe class Main
{
    public static bool ShouldExit = false;
    public static string? Profile;
    
    private static ImGuiContextPtr _context;
    private static Client _client;
    private static ImFontPtr _fontRegular;
    private static ImFontPtr _fontBold;

    private static bool _uiFlag_IsVisibleDialogEvent = false;
    private static bool _uiFlag_IsVisibleCentralText = false;
    private static string _uiData_TextTitleDialogEvent = "";
    private static string _uiData_TextSubtitleDialogEvent = "";
    private static string _uiData_TitleDialogEvent = "";
    private static string _uiData_TextCentralText = "";

    private static Timer _timerTextCentral = new Timer() {AutoReset = false};
    
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int MessageBox(IntPtr hWnd, string text, string caption, uint type);

    public static void ShowError(string title, string text)
    {
        MessageBox(IntPtr.Zero, text, $"[KBS] {title}", 0x10 | 0x0);
    }
    
    [DllImport("kernel32.dll", EntryPoint = "OutputDebugStringA")]
    public static extern void OutputDebugStringA(string text);

    public static void Print(string text)
    {
        Main.OutputDebugStringA($"[{Program.TITLE}] {text}\n");
    }
    
    public static string GetKeyHash()
    {
        try
        {
            using (RegistryKey baseKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry32))
            using (RegistryKey key = baseKey.OpenSubKey(@"SOFTWARE\Electronic Arts\EA GAMES\Battlefield 2142\ergc", false))
            {
                if (key == null) return null;
                
                object valueObj = key.GetValue(null);
                if (valueObj == null) return null;

                string fullString = valueObj.ToString();
                if (fullString.Length <= 5) return null;

                string stringForHash = fullString.Substring(5);

                using (MD5 md5 = MD5.Create())
                {
                    byte[] hashBytes = md5.ComputeHash(Encoding.UTF8.GetBytes(stringForHash));
                    return BitConverter.ToString(hashBytes).Replace("-", "").ToLowerInvariant();
                }
            }
        }
        catch
        {
            return null;
        }
    }
    
    public static string GetLocale()
    {
        const string subKeyPath = @"SOFTWARE\Electronic Arts\EA GAMES\Battlefield 2142";
        const string valueName = "Locale";

        try
        {
            using (RegistryKey baseKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry32))
            using (RegistryKey key = baseKey.OpenSubKey(subKeyPath))
            {
                if (key == null) return null;
                object value = key.GetValue(valueName);
                return value?.ToString();
            }
        }
        catch
        {
            return null;
        }
    }

    public static void ShowDialog(DialogType type, string? txt = null)
    {
        if (type == DialogType.Ban)
        {
            _uiData_TextTitleDialogEvent = P.Get("reason.ban");
            _uiData_TitleDialogEvent = P.Get("dialog.title.lostconn").ToUpper();
        } else if (type == DialogType.Kick)
        {
            _uiData_TextTitleDialogEvent = P.Get("reason.kick");
            _uiData_TitleDialogEvent = P.Get("dialog.title.lostconn").ToUpper();
        } else if (type == DialogType.Other)
        {
            _uiData_TextTitleDialogEvent = "";
            _uiData_TitleDialogEvent = P.Get("dialog.title.notification").ToUpper();
        } 
        
        _uiFlag_IsVisibleDialogEvent = true;
        _uiData_TextSubtitleDialogEvent = txt == null ? "" : txt;
    }

    public static void ShowTextCentral(string text, TimeSpan period)
    {
        if (_timerTextCentral.Enabled) _timerTextCentral.Stop();

        _uiData_TextCentralText = text;
        _uiFlag_IsVisibleCentralText = true;
        
        _timerTextCentral.Interval = period.TotalMilliseconds < 1 ? Program.CENTRAL_TEXT_PERIOD.TotalMilliseconds : period.TotalMilliseconds; 
        _timerTextCentral.Elapsed += ( sender, e ) => _uiFlag_IsVisibleCentralText = false;
        _timerTextCentral.Start();
    }
    
    public static string? GetProfile()
    {
        IntPtr address = new IntPtr(0x00A228B9);
        string? result = Marshal.PtrToStringAnsi(address);
        if (result == null || result.Length >= 32) return null;
        return result.Trim();
    }

    public static void TaskProfileTracker()
    {
        Profile = GetProfile();
        string? profile;
        while (!ShouldExit)
        {
            profile = GetProfile();
            if (profile != Profile)
            {
                Profile = profile;
                
                if (Profile != null)
                {
                    Main._client.Send(Protocol.PkgUpdateProfile(Profile).GetBytes());
                    Print($"profile updated: `{Profile}`");
                }
            }
            Thread.Sleep(TimeSpan.FromMilliseconds(100));
        }
    }
    
    public static bool IsIPv4(string ipString)
    {
        if (string.IsNullOrWhiteSpace(ipString) || ipString.Split('.').Length != 4) return false;
        return IPAddress.TryParse(ipString, out _);
    }
    
    [UnmanagedCallersOnly(EntryPoint = "OnStart")]
    public static void OnStart()
    {
        Main.Print("start");
        Program.LANG = Main.GetLocale() ?? "en";
        Main.Print($"Lang `{Program.LANG}`");
        
        string[] args = Environment.GetCommandLineArgs();
        if (args.Contains("+kbsaddr"))
        {
            int index = args.IndexOf("+kbsaddr");
            if (index > -1 && index+1 <= args.Length-1 && IsIPv4(args[index+1]))
            {
                Program.ADDRESS = args[index+1];
            }
            else
            {
                ShowError(P.Get("msg.err.invarg.title"), P.Get("msg.err.invargaddr.txt"));
            }
        }
        
        if (args.Contains("+kbsport"))
        {
            int index = args.IndexOf("+kbsport");
            ushort port;
            if (index > -1 && index+1 <= args.Length-1 && ushort.TryParse(args[index+1], out port))
            {
                Program.PORT = port;
            }
            else
            {
                ShowError(P.Get("msg.err.invarg.title"), P.Get("msg.err.invarport.txt"));
            }
        }
        
        Main._client = new(Program.ADDRESS, Program.PORT);
        
        Main._client.OnConnected += OnConnected;
        Main._client.OnDisconnected += OnDisconnected;
        Main._client.OnReceive += OnReceive;
        Main._client.OnError += OnError;
        
        Main._client.Start();
        
        Print($"Client works with {Program.ADDRESS}:{Program.PORT}");

        Thread taskpt = new Thread(TaskProfileTracker);
        taskpt.Start();
    }
    
    public static void OnConnected()
    {
        Main.Print("Connected");
        Main._client.Send(Protocol.PkgAuth(Program.VERSION, Main.GetKeyHash()).GetBytes());
    }

    public static void OnDisconnected()
    {
        Main.Print("Disconnected");
    }

    public static void OnError(Exception ex)
    {
        Main.Print($"Error: {ex.Message}\n{ex.StackTrace}");
    }

    public static void OnReceive(byte[] data)
    {
        Package? pkg = Package.ValidatePackage(data);
        
        if (pkg == null)
        {
            Print("An invalid packet was received from the server. It has been discarded");
            return;
        }
        
        Main.Print($"<< type {pkg.Type}, header {pkg.Header} ({data.Length})");

        foreach (Package p in Protocol.Get(pkg))
        {
            Main._client.Send(p.GetBytes());
            Main.Print($">> type {p.Type}, header {p.Header} ({p.GetBytes().Length})");
        }
    }

    [UnmanagedCallersOnly(EntryPoint = "OnStop")]
    public static void OnStop()
    {
        ShouldExit = true;
        Main._client.Stop();
        Main._client.Dispose();
        Main.Print("stop");
    }
    
    [UnmanagedCallersOnly(EntryPoint = "OnResetInvalidateDeviceObjects", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static void OnResetInvalidateDeviceObjects(int init)
    {
        try
        {
            //Print("OnResetInvalidateDeviceObjects 1");
            ImGuiImplD3D9.InvalidateDeviceObjects();
            //Print("OnResetInvalidateDeviceObjects 2");
        }
        catch (Exception ex)
        {
            Print(ex.ToString());
        }
    }
    
    [UnmanagedCallersOnly(EntryPoint = "OnResetCreateDeviceObjects", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static void OnResetCreateDeviceObjects(int init)
    {
        try
        {
            //Print("OnResetCreateDeviceObjects 1");
            ImGuiImplD3D9.CreateDeviceObjects();
            //Print("OnResetCreateDeviceObjects 2");
        }
        catch (Exception ex)
        {
            Print(ex.ToString());
        }
    }
    
    [UnmanagedCallersOnly(EntryPoint = "OnInitImgui", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static void OnInitImgui(int init, nint device, nint hwnd)
    {
        try
        {
            //Print("OnInitImgui 1");

            if (init != 0)
                return;

            _context = ImGui.CreateContext();

            ImGuiImplWin32.SetCurrentContext(_context);
            ImGuiImplWin32.Init((void*)hwnd);

            ImGuiImplD3D9.SetCurrentContext(_context);
            ImGuiImplD3D9.Init(new((IDirect3DDevice9*)device));

            //Print("OnInitImgui 2");
        }
        catch (Exception ex)
        {
            Print(ex.ToString());
        }
    }
    
    [UnmanagedCallersOnly(EntryPoint = "OnShutdownImgui", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static void OnShutdownImgui(int init)
    {
        try
        {
            //Print("OnShutdownImgui 1");

            if (init == 0)
                return;

            ImGuiImplD3D9.Shutdown();
            ImGuiImplWin32.Shutdown();
            ImGui.DestroyContext();

            //Print("OnShutdownImgui 2");
        }
        catch (Exception ex)
        {
            Print(ex.ToString());
        }
    }
    
    [UnmanagedCallersOnly(EntryPoint = "OnWndProcImplWin32", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static nint OnWndProcImplWin32(int init, nint hWnd, uint msg, nuint wParam, nint lParam)
    {
        try
        {
            //Print("OnWndProcImplWin32 1");
            nint result = ImGuiImplWin32.WndProcHandler(hWnd, msg, wParam, lParam);
            //Print("OnWndProcImplWin32 2");
            return result;
        }
        catch (Exception ex)
        {
            Print(ex.ToString());
            return 0;
        }
    }
    
    [UnmanagedCallersOnly(EntryPoint = "OnBeginImgui", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static void OnBeginImgui(int init, nint device)
    {
        ImGuiIOPtr io = ImGui.GetIO();
        io.ConfigFlags |= ImGuiConfigFlags.NoMouseCursorChange;
        Main._fontRegular = io.Fonts.AddFontFromFileTTF("Roboto-Regular.ttf");
        Main._fontBold = io.Fonts.AddFontFromFileTTF("Roboto-Bold.ttf");
        Main.Print("OnBeginImgui");
    }
    
    [UnmanagedCallersOnly(EntryPoint = "OnEndScene", CallConvs = new[] { typeof(CallConvCdecl) })]
    public static void OnEndScene(int init)
    {

        ImGuiImplD3D9.NewFrame();
        ImGuiImplWin32.NewFrame();
        ImGui.NewFrame();
        
        ImGui.PushStyleColor(ImGuiCol.WindowBg, 0xFF404040u);
        ImGui.PushStyleColor(ImGuiCol.MenuBarBg, 0xFF00FFFFu);
        
        if (_uiFlag_IsVisibleDialogEvent)
        {
            ImGui.SetNextWindowSize(new Vector2(550, 300), ImGuiCond.FirstUseEver);
            ImGui.SetNextWindowPos(new Vector2((ImGui.GetMainViewport().Size.X / 2) - (550.0f / 2), (ImGui.GetMainViewport().Size.Y / 2) - (300.0f / 2)));
            if (ImGui.Begin("Connection lost###KbMsgForm", ImGuiWindowFlags.NoCollapse | ImGuiWindowFlags.NoResize | ImGuiWindowFlags.NoTitleBar))
            {
                ImGui.SetNextFrameWantCaptureKeyboard(true);
                if (ImGui.Shortcut((int)ImGuiKey.LeftCtrl))
                {
                    _uiFlag_IsVisibleDialogEvent = false;
                }
                
                ImGui.PushFont(Main._fontBold, 20f);
                ImGui.TextUnformatted(_uiData_TitleDialogEvent);
                ImGui.PopFont();
            
                ImGui.PushStyleColor(ImGuiCol.ChildBg, 0xFF363636u);
                if (ImGui.BeginChild("child1", new Vector2(-1, 220),  ImGuiChildFlags.AlwaysUseWindowPadding | ImGuiChildFlags.NavFlattened, ImGuiWindowFlags.NoSavedSettings))
                {
                    if (_uiData_TextTitleDialogEvent.Trim() != "")
                    {
                        ImGui.PushFont(null, 20f);
                        ImGui.TextUnformatted(_uiData_TextTitleDialogEvent);
                        ImGui.PopFont();
                    }
                    
                    ImGui.PushFont(null, 20f);
                    ImGui.TextUnformatted(_uiData_TextSubtitleDialogEvent);
                    ImGui.PopFont();
                }
                ImGui.EndChild();
                ImGui.PopStyleColor();
            
                Vector2 windowPos  = ImGui.GetWindowPos();
                Vector2 windowSize = ImGui.GetWindowSize();
                float bottomY = windowPos.Y + windowSize.Y;
            
                ImGui.SetCursorScreenPos(new Vector2(windowPos.X + 7f, bottomY - 33f));
                ImGui.PushFont(null, 14f);
                ImGui.PushStyleColor(ImGuiCol.Text, 0xFF808080u);
                ImGui.TextUnformatted(P.Get("dialog.txt1"));
                ImGui.PopStyleColor();
                ImGui.PopFont();
            
                ImGui.SetCursorScreenPos(new Vector2(windowPos.X + windowSize.X - 117f, bottomY - 40f));
                ImGui.PushStyleColor(ImGuiCol.Button, 0xFF808080u);
                if (ImGui.Button(P.Get("dialog.btn.close"), new Vector2(104, 0)))
                {
                    _uiFlag_IsVisibleDialogEvent = false;
                }
                ImGui.PopStyleColor();
            }
            
            ImGui.End();
        }

        if (_uiFlag_IsVisibleCentralText)
        {
            ImDrawListPtr draw_list = ImGui.GetBackgroundDrawList();
            Vector2 display_size = ImGui.GetIO().DisplaySize;
            
            Vector2 text_size = ImGui.CalcTextSize(_uiData_TextCentralText);
            
            Vector2 pos1 = new Vector2(
                (display_size.X - text_size.X) * 0.5f,
                (display_size.Y - text_size.Y) * 0.5f - 30
            );
            
            Vector2 pos2 = new Vector2(
                (display_size.X - text_size.X) * 0.5f + 1,
                (display_size.Y - text_size.Y) * 0.5f - 29
            );
            
            draw_list.AddText(Main._fontBold, 24, pos2, 0xFF454545u, _uiData_TextCentralText);
            draw_list.AddText(Main._fontBold, 24, pos1, 0xFFFCFCFCu, _uiData_TextCentralText);
        }

        ImGui.PopStyleColor(2);

        ImGui.Render();
        ImGuiImplD3D9.RenderDrawData(ImGui.GetDrawData());
            
    }
}