using CIA.Net.Public.Bot.Configuration;
using CIA.Net.Public.Bot.Handlers;
using Discord;
using Discord.WebSocket;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace CIA.Net.Public.Bot
{
    public class CIABotClient
    {
        private readonly DiscordSocketClient _client;
        private readonly CommandHandler _commandHandler;
        private readonly ILogger<CIABotClient> _logger;
        private readonly CIABotOptions _options;

        public CIABotClient(IOptions<CIABotOptions> options, ILogger<CIABotClient> logger, DiscordSocketClient client, CommandHandler commandHandler)
        {
            _options = options.Value;
            _logger = logger;
            _client = client;
            _commandHandler = commandHandler;

            _client.Log += LogAsync;
        }

        public async Task StartAsync()
        {
            if (string.IsNullOrEmpty(_options.Token))
            {
                _logger.LogError("Bot token is missing or empty. Check the Token configuration.");
                throw new InvalidOperationException("Bot token is missing.");
            }

            _logger.LogInformation("Starting the bot with token: {Token}", _options.Token.Substring(0, 4) + "****");

            try
            {
                await _client.LoginAsync(TokenType.Bot, _options.Token);
                await _client.StartAsync();

                await _commandHandler.InitializeAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred while starting the bot.");
                throw;
            }
        }

        private Task LogAsync(LogMessage logMessage)
        {
            _logger.LogInformation(logMessage.ToString());
            return Task.CompletedTask;
        }
    }
}
