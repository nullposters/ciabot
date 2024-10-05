using CIA.Net.Public.Bot.Configuration;
using CIA.Net.Public.Bot.Handlers;
using Discord.Interactions;
using Discord.WebSocket;
using Discord;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Net.NetworkInformation;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Serilog;
using Serilog.Sinks.Syslog;

namespace CIA.Net.Public.Bot.Extensions
{
    public static class ServiceCollectionExtensions
    {
        public static IServiceCollection AddAndConfigureBotServices(this IServiceCollection services, IConfiguration configuration)
        {
            services.AddOptions(configuration);
            services.AddSingleton(sp =>
            {
                var client = new DiscordSocketClient(new DiscordSocketConfig
                {
                    GatewayIntents = GatewayIntents.AllUnprivileged | GatewayIntents.MessageContent
                });
                return client;
            });
            services.AddSingleton(sp =>
            {
                var client = sp.GetRequiredService<DiscordSocketClient>();
                return new InteractionService(client);
            });
            services.AddHandlers();
            services.AddSerilog();

            return services;
        }

        private static IServiceCollection AddSerilog(this IServiceCollection services)
        {
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

            return services;
        }

        private static IServiceCollection AddOptions(this IServiceCollection services, IConfiguration configuration)
        {
            services.Configure<BotConfigurationOptions>(configuration.GetSection(BotConfigurationOptions.SettingsName));
            services.Configure<CIABotOptions>(configuration.GetSection(CIABotOptions.SettingsName));
            services.Configure<PaperTrailLoggingOptions>(configuration.GetSection(PaperTrailLoggingOptions.SettingsName));

            return services;
        }
        private static IServiceCollection AddHandlers(this IServiceCollection services)
        {
            services.AddSingleton<SettingsManager>();
            services.AddSingleton<CommandHandler>();
            services.AddSingleton<MessageHandler>();
            services.AddSingleton<CIABotClient>();

            return services;
        }
    }
}
