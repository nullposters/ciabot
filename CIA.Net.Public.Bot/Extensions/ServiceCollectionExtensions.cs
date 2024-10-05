using CIA.Net.Public.Bot.Configuration;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CIA.Net.Public.Bot.Extensions
{
    public static class ServiceCollectionExtensions
    {
        public static IServiceCollection AddSettingsManager(this IServiceCollection services, IConfiguration configuration)
        {
            services.Configure<BotConfiguration>(configuration.GetSection(BotConfiguration.SettingsName));
            services.AddSingleton<SettingsManager>();
            return services;
        }

        public static IServiceCollection AddBotClient(this IServiceCollection services, IConfiguration configuration)
        {
            services.Configure<CIABotOptions>(configuration.GetSection(CIABotOptions.SettingsName));
            services.AddSingleton<CIABotClient>();
            return services;
        }
    }
}
