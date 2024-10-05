using Discord;
using Discord.WebSocket;
using Microsoft.Extensions.Logging;

namespace CIA.Net.Public.Bot.Handlers
{
    public class MessageHandler
    {
        private readonly SettingsManager _settingsManager;
        private readonly ILogger<MessageHandler> _logger;
        private static readonly List<string> Redactions =
        [
            "`[REDACTED]`", "`[EXPUNGED]`", "`[CLASSIFIED]`", "`[REDACTED BY CIA]`",
            "`[REDACTED BY FBI]`", "`[REDACTED BY NSA]`", "`[REDACTED BY DHS]`",
            "`[REDACTED BY MI6]`", "`[REDACTED BY KGB]`", "`********`", "`████████`"
        ];

        public MessageHandler(SettingsManager settingsManager, ILogger<MessageHandler> logger)
        {
            _settingsManager = settingsManager;
            _logger = logger;
        }

        public bool IsBotActionAllowedInChannel(SocketMessage message)
        {
            var settings = _settingsManager.Settings;
            bool isChannelInBlacklist = settings.ChannelBlacklist.Contains(message.Channel.Id.ToString());
            bool isTimedOut = settings.TimeoutExpiration > DateTimeOffset.UtcNow.ToUnixTimeSeconds();

            return !(isChannelInBlacklist || isTimedOut);
        }

        public string RedactMessage(SocketMessage message, List<int> triggerWordIndices)
        {
            var settings = _settingsManager.Settings;
            var messageContent = message.Content.Split(' ').ToList();
            var indices = triggerWordIndices.Any() ? triggerWordIndices : Enumerable.Range(0, messageContent.Count).ToList();
            double threshold = triggerWordIndices.Any() ? settings.TriggerWordChance : settings.RedactionChance;

            bool wasRedacted = false;
            foreach (var idx in indices)
            {
                if (new Random().NextDouble() < threshold)
                {
                    messageContent[idx] = Redactions[new Random().Next(Redactions.Count)];
                    wasRedacted = true;
                }
            }

            if (!wasRedacted)
            {
                int randomIndex = new Random().Next(indices.Count);
                messageContent[indices[randomIndex]] = Redactions[new Random().Next(Redactions.Count)];
            }

            return string.Join(" ", messageContent);
        }

        public async Task RunMessageRedaction(SocketMessage message)
        {
            var settings = _settingsManager.Settings;
            bool hasBypassCharacter = message.Content.StartsWith(settings.BypassPrefix);
            bool hasImage = message.Attachments.Any(attachment => attachment.ContentType.StartsWith("image/"));
            bool isWhitelistEnabled = settings.ChannelWhitelist.Any();
            bool isChannelInWhitelist = settings.ChannelWhitelist.Contains(message.Channel.Id.ToString());
            bool isChannelInBlacklist = settings.ChannelBlacklist.Contains(message.Channel.Id.ToString());
            bool isTimedOut = settings.TimeoutExpiration > DateTimeOffset.UtcNow.ToUnixTimeSeconds();

            if (hasBypassCharacter || hasImage || isChannelInBlacklist || isTimedOut || (isWhitelistEnabled && !isChannelInWhitelist))
                return;

            var triggerWordIndices = message.Content.ToLower().Split(' ')
                .Select((word, index) => settings.TriggerWords.Contains(word) ? index : -1)
                .Where(index => index != -1).ToList();

            if (triggerWordIndices.Any() || new Random().NextDouble() < settings.RedactionChance)
            {
                var redactedMessage = RedactMessage(message, triggerWordIndices);
                try
                {
                    await message.DeleteAsync();
                    await message.Channel.SendMessageAsync($"<@{message.Author.Id}>:\n{redactedMessage}");
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Error redacting message: {ex}");
                }
            }
        }

        public async Task RunReactions(SocketMessage message)
        {
            if (!message.Content.Contains("http"))
            {
                if (message.Content.Contains("js", StringComparison.CurrentCultureIgnoreCase))
                {
                    try
                    {
                        await ReactWithFunnyLetters(message, "bad");
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Error while reacting to message: {ex}");
                    }
                }

                if (message.Author.Id == 284876500480557056 && new Random().Next(1, 6) == 1)
                {
                    try
                    {
                        await ReactWithFunnyLetters(message, "lib");
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Error while reacting to message: {ex}");
                    }
                }
            }
        }

        private async Task ReactWithFunnyLetters(SocketMessage message, string text)
        {
            var upperText = text.ToUpper();

            foreach (var c in upperText)
            {
                if (char.IsLetter(c))
                {
                    try
                    {
                        var emoji = new Emoji(GetRegionalIndicatorEmoji(c));
                        await message.AddReactionAsync(emoji);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Error while reacting to message: {ex}");
                    }
                }
            }
        }

        private string GetRegionalIndicatorEmoji(char letter)
        {
            int offset = char.ToUpper(letter) - 'A';
            int unicodeValue = 0x1F1E6 + offset;  // Unicode for regional indicator symbol starts at 0x1F1E6
            return char.ConvertFromUtf32(unicodeValue);
        }
    }
}
