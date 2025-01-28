// Modified Program.cs
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;

class Program
{
    static async Task Main(string[] args)
    {
        try
        {
            var config = Config.Load("config.json");
            var listener = new TcpListener(IPAddress.Any, config.Port);
            listener.Start();
            
            Console.WriteLine($"Listening on port {config.Port}...");

            while (true)
            {
                var client = await listener.AcceptTcpClientAsync();
                Console.WriteLine($"Connected to: {client.Client.RemoteEndPoint}");
                _ = HandleClientAsync(client);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
        }
    }

    private static async Task HandleClientAsync(TcpClient client)
    {
         string clientInfo = client.Client.RemoteEndPoint?.ToString() ?? "unknown client";
        
        try
        {
            using (client)
            using (var stream = client.GetStream())
            {
                // Fix 1: Handle network byte order for header length
                var headerLengthBytes = await NetworkHelper.ReadBytesAsync(stream, 4);
                var headerLength = IPAddress.NetworkToHostOrder(BitConverter.ToInt32(headerLengthBytes, 0));

                // Restrict maximum header size for security
                if (headerLength < 0 || headerLength > 10 * 1024 * 1024) // 10MB max
                {
                    throw new InvalidDataException("Invalid header size");
                }

                var headerBytes = await NetworkHelper.ReadBytesAsync(stream, headerLength);
                var headerJson = Encoding.UTF8.GetString(headerBytes);





                Console.WriteLine($"Raw JSON received: {headerJson}");  // Debug log
                
                     var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true, // Handle case differences
                AllowTrailingCommas = true
            };

            List<FileMetadata> files;
            try
            {
                files = JsonSerializer.Deserialize<List<FileMetadata>>(headerJson, options) 
                    ?? throw new InvalidDataException("Empty file list");
            }
            catch (JsonException ex)
            {
                throw new InvalidDataException($"Invalid JSON format: {ex.Message}");
            }

            if (files.Count == 0)
            {
                throw new InvalidDataException("No files specified in header");
            }


                var timestamp = DateTime.Now.ToString("yyyyMMddHHmmssfff");
                var directoryPath = Path.Combine("ReceivedData", timestamp);
                Directory.CreateDirectory(directoryPath);

                foreach (var file in files)
                {
                    // Fix 2: Validate file name and size
                    var fileName = Path.GetFileName(file.Name); // Sanitize file name
                    if (string.IsNullOrWhiteSpace(fileName))
                    {
                        throw new InvalidDataException("Invalid file name");
                    }

                    if (file.Size <= 0 || file.Size > 100 * 1024 * 1024) // 100MB max per file
                    {
                        throw new InvalidDataException($"Invalid file size for {fileName}");
                    }

                    var filePath = Path.Combine(directoryPath, fileName);
                    var fileData = await NetworkHelper.ReadBytesAsync(stream, file.Size);

                    // Save with original extension
                    if (file.Type == "text/plain")
                    {
                        await File.WriteAllTextAsync(filePath, Encoding.UTF8.GetString(fileData));
                    }
                    else
                    {
                        await File.WriteAllBytesAsync(filePath, fileData);
                    }

                    Console.WriteLine($"Saved: {fileName} ({fileData.Length} bytes)");
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error from {clientInfo}: {ex.Message}");
        }
        finally
        {
            Console.WriteLine($"Disconnected: {clientInfo}");
        }
    }
}