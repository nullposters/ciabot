using Discord.Interactions;
using Discord.WebSocket;
using Microsoft.Extensions.Logging;
using System;
using System.Reflection;

namespace CIA.Net.Public.Bot.Handlers
{
    public class CommandHandler
    {
        private readonly DiscordSocketClient _client;
        private readonly InteractionService _interactionService;
        private readonly SettingsManager _settingsManager;
        private readonly ILogger<CommandHandler> _logger;
        private readonly IServiceProvider _serviceProvider;

        public CommandHandler(DiscordSocketClient client, InteractionService interactionService, SettingsManager settingsManager, ILogger<CommandHandler> logger, IServiceProvider serviceProvider)
        {
            _client = client;
            _interactionService = interactionService;
            _settingsManager = settingsManager;
            _logger = logger;
            _serviceProvider = serviceProvider;

            _client.Ready += OnReadyAsync;
            _client.InteractionCreated += HandleInteractionAsync;
        }

        public async Task InitializeAsync()
        {
            await _interactionService.AddModulesAsync(Assembly.GetExecutingAssembly(), _serviceProvider);
        }

        private async Task OnReadyAsync()
        {
            foreach (var guild in _client.Guilds)
            {
                await _interactionService.RegisterCommandsToGuildAsync(guild.Id, true);
            }
            _logger.LogInformation("Slash commands registered and ready.");
        }

        private async Task HandleInteractionAsync(SocketInteraction interaction)
        {
            try
            {
                var context = new SocketInteractionContext(_client, interaction);
                await _interactionService.ExecuteCommandAsync(context, _serviceProvider);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error handling slash command interaction.");
            }
        }
    }
}
