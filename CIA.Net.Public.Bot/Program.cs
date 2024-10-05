using CIA.Net.Public.Bot;
using CIA.Net.Public.Bot.Configuration;
using CIA.Net.Public.Bot.Extensions;
using CIA.Net.Public.Bot.Handlers;
using Discord;
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
                .ConfigureServices((context, services) => services.AddAndConfigureBotServices(context.Configuration));

            var host = hostBuilder.Build();

            var bot = host.Services.GetRequiredService<CIABotClient>();
            await bot.StartAsync();

            await Task.Delay(-1);
        }
    }
}
