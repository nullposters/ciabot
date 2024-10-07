using CIA.Net.Public.Bot;
using CIA.Net.Public.Bot.Extensions;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;


namespace CIA.Net.Public
{
    internal class Program
    {
        public static async Task Main(string[] args)
        {
            var hostBuilder = Host.CreateDefaultBuilder(args)
                .ConfigureAppConfiguration((context, config) =>
                {
                    config
                    .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
                    .AddJsonFile("appsettings.local.json", optional: false, reloadOnChange: true);
                })
                .ConfigureServices((context, services) => services.AddAndConfigureBotServices(context.Configuration));

            var host = hostBuilder.Build();

            var bot = host.Services.GetRequiredService<CIABotClient>();
            await bot.StartAsync();

            await Task.Delay(-1);
        }
    }
}
