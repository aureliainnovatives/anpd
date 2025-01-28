// Config.cs
using System.Text.Json;

public class Config
{
    public int Port { get; set; }

    public static Config Load(string path)
    {
        var json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<Config>(json) ?? throw new InvalidDataException("Invalid config file");
    }
}