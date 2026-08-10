namespace speaker;

public class Phrases
{
    private static Dictionary<string, string> GetDict()
    {
        switch (Program.LANG)
        {
            case "en":
            {
                return Phrases.En;
            }
            case "ru":
            {
                return Phrases.Ru;
            }
            default: throw new Exception($"Language code `{Program.LANG}` is incorrect");
        }
    }
    
    public static string Get(string phrase)
    {
        string? result;
        if (!Phrases.GetDict().TryGetValue(phrase, out result)) throw new Exception($"Phrase `{phrase}` in dictionary of language `{Program.LANG}` not found");
        return result;
    }
    
    private static Dictionary<string, string> En = new ()
    {
        {"dialog.title.lostconn", "lost connection"},
        {"dialog.btn.close", "Close"},
        {"dialog.txt1", "To close the window, press CTRL"},
        {"reason.ban", "You are banned on this server"},
        {"msg.err.invarg.title", "Invalid argument"},
        {"msg.err.invargaddr.txt", "The kbsaddr argument contains no value or the value is invalid. A value in IPv4 format (XXX.XXX.XXX.XXX) is allowed"},
        {"msg.err.invarport.txt", "The kbsport argument contains no value or the value is invalid. A value from 1 to 65535 is allowed"}
    };
    
    private static Dictionary<string, string> Ru = new ()
    {
        {"dialog.title.lostconn", "подключение потеряно"},
        {"dialog.btn.close", "Закрыть"},
        {"dialog.txt1", "Закрыть окно можно нажав CTRL"},
        {"reason.ban", "Вы заблокированы на этом сервере"},
        {"msg.err.invarg.title", "Некорректный аргумент"},
        {"msg.err.invargaddr.txt", "Аргумент kbsaddr не содержит значения или оно некорректное. Допустимо значение в формате IPv4 (XXX.XXX.XXX.XXX)"},
        {"msg.err.invarport.txt", "Аргумент kbsport не содержит значения или оно некорректное. Допустимо значение от 1 до 65535"}
    };
}