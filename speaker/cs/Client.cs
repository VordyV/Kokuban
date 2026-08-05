using System.Net.Sockets;

namespace speaker;

public sealed class Client : IDisposable
{
    public Action? OnConnected;
    public Action? OnDisconnected;
    public Action<Exception>? OnError;
    public Action<byte[]>? OnReceive;

    public bool Connected => _client?.Connected ?? false;

    private readonly string _host;
    private readonly int _port;
    private readonly TimeSpan _reconnectDelay;

    private TcpClient? _client;
    private NetworkStream? _stream;
    private CancellationTokenSource? _cts;

    public Client(string host, int port, TimeSpan? reconnectDelay = null)
    {
        _host = host;
        _port = port;
        _reconnectDelay = reconnectDelay ?? TimeSpan.FromSeconds(3);
    }

    public void Start()
    {
        if (_cts != null)
            return;

        _cts = new CancellationTokenSource();
        _ = RunAsync(_cts.Token);
    }

    public void Stop()
    {
        _cts?.Cancel();
        _client?.Dispose();
        _cts = null;
    }

    public async Task SendAsync(byte[] data)
    {
        if (_stream == null)
            return;

        await _stream.WriteAsync(data);
    }

    public void Send(byte[] data)
    {
        Task.Run(async () => await this.SendAsync(data));
    }

    private async Task RunAsync(CancellationToken token)
    {
        byte[] buffer = new byte[8192];
        
        bool wasConnected = false;

        while (!token.IsCancellationRequested)
        {
            try
            {
                _client = new TcpClient();
                await _client.ConnectAsync(_host, _port, token);

                wasConnected = true;
                
                _stream = _client.GetStream();
                OnConnected?.Invoke();

                while (!token.IsCancellationRequested)
                {
                    int count = await _stream.ReadAsync(buffer, token);

                    if (count == 0)
                        break;

                    var data = new byte[count];
                    Buffer.BlockCopy(buffer, 0, data, 0, count);

                    OnReceive?.Invoke(data);
                }
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                OnError?.Invoke(ex);
            }
            finally
            {
                _stream?.Dispose();
                _client?.Dispose();

                _stream = null;
                _client = null;

                if (wasConnected)
                {
                    OnDisconnected?.Invoke();
                    wasConnected = false;
                }
            }

            try
            {
                await Task.Delay(_reconnectDelay, token);
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }
    }

    public void Dispose()
    {
        Stop();
    }
}