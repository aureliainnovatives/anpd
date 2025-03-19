// NetworkHelper.cs
using System;
using System.IO;
using System.Net.Sockets;
using System.Threading.Tasks;

public static class NetworkHelper
{
    public static async Task<byte[]> ReadBytesAsync(NetworkStream stream, int count)
    {
        var buffer = new byte[count];
        var bytesRead = 0;
        
        while (bytesRead < count)
        {
            var remaining = count - bytesRead;
            var read = await stream.ReadAsync(buffer, bytesRead, remaining);
            if (read == 0)
                throw new EndOfStreamException();
            bytesRead += read;
        }
        
        return buffer;
    }
}