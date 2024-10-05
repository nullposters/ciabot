using CIA.Net.Public.Bot;
using CIA.Net.Public.Bot.Configuration;
using CIA.Net.Public.Bot.Extensions;
using CIA.Net.Public.Bot.Handlers;
using Discord.Interactions;
using Discord.WebSocket;
using Microsoft.EntityFrameworkCore.Diagnostics.Internal;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Serilog;
using Serilog.Sinks.Syslog;


namespace CIA.Net.Public
{
    internal class Program
    {
        public static async Task Main(string[] args)
        {
            var hostBuilder = Host.CreateDefaultBuilder(args)
                .ConfigureAppConfiguration((context, config) =>
                {
                    config.AddJsonFile("appsettings.json", optional: false, reloadOnChange: true);
                })
                .ConfigureServices((context, services) =>
                {
                    services.Configure<BotConfiguration>(context.Configuration.GetSection(BotConfiguration.SettingsName));
                    services.Configure<PaperTrailLoggingOptions>(context.Configuration.GetSection(PaperTrailLoggingOptions.SettingsName));
                    services.Configure<CIABotOptions>(context.Configuration.GetSection(CIABotOptions.SettingsName));
                    services.AddSingleton<SettingsManager>();
                    services.AddSingleton<DiscordSocketClient>();
                    services.AddSingleton(sp =>
                    {
                        var client = sp.GetRequiredService<DiscordSocketClient>();
                        return new InteractionService(client);
                    });
                    services.AddSingleton<CommandHandler>();
                    services.AddSingleton<CIABotClient>();
                    services.AddSingleton<ILoggerProvider>(sp =>
                    {
                        var options = sp.GetRequiredService<IOptions<PaperTrailLoggingOptions>>().Value;

                        var logger = new LoggerConfiguration()
                            .WriteTo.Console()
                            .WriteTo.Syslog(options.Destination, options.Port, System.Net.Sockets.ProtocolType.Tcp)
                            .Enrich.WithProperty("hostname", Environment.MachineName)
                            .CreateLogger();

                        Log.Logger = logger;
                        return new Serilog.Extensions.Logging.SerilogLoggerProvider(logger);
                    });

                    services.AddLogging();
                });

            var host = hostBuilder.Build();

            var bot = host.Services.GetRequiredService<CIABotClient>();
            await bot.StartAsync();

            await Task.Delay(-1);
        }
    }
}
