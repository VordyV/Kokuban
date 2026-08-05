using System.Text.Json;
using System.Text.Json.Serialization;

namespace speaker;

public enum PackageType
{
    Request = 0,
    Response = 1,
    Auth = 2,
    Error = 3
}

public enum ErrorType
{
    IncorrectPacketFormat = 0,
    RequestHeaderInvalid = 1,
    NoAuthData = 2,
    IncorrectAuthData = 3,
    ReAuth = 4,
    IncorrectKeyHash = 5
    
}

public sealed class Package
{
    [JsonPropertyName("type")]
    public PackageType Type { get; set; }

    [JsonPropertyName("header")]
    public string? Header { get; set; }

    [JsonPropertyName("body")]
    public Dictionary<string, object?> Body { get; set; } = new();


    public byte[] GetBytes()
    {
        var json = JsonSerializer.SerializeToUtf8Bytes(this, PackageJsonContext.Default.Package);
        var result = new byte[json.Length + 1];
        json.CopyTo(result, 0);
        result[^1] = (byte)'\n';
        return result;
    }

    public static Package? ValidatePackage(ReadOnlySpan<byte> data)
    {
        try
        {
            if (data.Length > 0 && data[^1] == (byte)'\n')
                data = data[..^1];
            if (data.Length > 0 && data[^1] == (byte)'\r')
                data = data[..^1];

            return JsonSerializer.Deserialize(data, PackageJsonContext.Default.Package);
        }
        catch
        {
            return null;
        }
    }

    public static Package CreatePkgError(ErrorType error)
    {
        return new Package
        {
            Type = PackageType.Error,
            Header = null,
            Body = new Dictionary<string, object?>
            {
                ["type"] = (int)error
            }
        };
    }

    public static Package CreatePkg(PackageType type, string header, Dictionary<string, object?> data)
    {
        return new Package
        {
            Type = type,
            Header = header,
            Body = data
        };
    }
}

[JsonSerializable(typeof(Package))]
[JsonSerializable(typeof(Dictionary<string, object?>))]
[JsonSourceGenerationOptions(
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    WriteIndented = false)]
internal partial class PackageJsonContext : JsonSerializerContext {}