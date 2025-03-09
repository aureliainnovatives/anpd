// Config.cs
using System;
using System.IO;
using System.Text.Json;

public class Config
{
    public int Port { get; set; }

    public static Config Load(string path)
    {
        var json = File.ReadAllText(path);
        var config = JsonSerializer.Deserialize<Config>(json);
        if (config == null)
            throw new InvalidDataException("Invalid config file");
        return config;
    }
}