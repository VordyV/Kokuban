namespace speaker;

public class Program
{
    public static readonly string TITLE = "KBS";
    public static string ADDRESS = "127.0.0.1";
    public static ushort PORT = 8080;
    public static string LANG = "ru";
    public static readonly string VERSION = "2.0";
    public static readonly TimeSpan CENTRAL_TEXT_PERIOD = TimeSpan.FromSeconds(7);
    public static readonly TimeSpan BOTTOM_STATUS_BAR_PERIOD = TimeSpan.FromSeconds(3);
}