
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

internal static class Program
{
    static async Task<int> Main(string[] args)
    {
        using var host = Host.CreateDefaultBuilder(args)
            .ConfigureServices((context, services) =>
            {
                services.AddLogging(builder =>
                {
                    builder.AddSimpleConsole(options =>
                    {
                        options.TimestampFormat = "[yyyy-MM-dd HH:mm:ss] ";
                        options.IncludeScopes = false;
                    });
                    builder.SetMinimumLevel(LogLevel.Information);
                    builder.AddFilter("System.Net.Http", LogLevel.Warning);
                });
                services.AddHttpClient();
                services.AddSingleton<App>();
            })
            .Build();

        var logger = host.Services.GetRequiredService<ILogger<App>>();
        var app = host.Services.GetRequiredService<App>();

        try
        {
            await host.StartAsync();
            var result = await app.RunOnceAsync();
            await host.StopAsync(CancellationToken.None);
            return result;
        }
        catch (OperationCanceledException)
        {
            logger.LogInformation("Cancelled");
            return 130;
        }
        catch (Exception ex)
        {
            logger.LogCritical(ex, "Unhandled error");
            return 1;
        }
    }
}