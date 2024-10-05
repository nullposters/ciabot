using CIA.Net.Public.Bot.Configuration;
using Discord;
using Discord.Interactions;
using Discord.WebSocket;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace CIA.Net.Public.Bot
{
    public class SlashCommandModule : InteractionModuleBase<SocketInteractionContext>
    {
        private readonly SettingsManager _settingsManager;
        private readonly ILogger<SlashCommandModule> _logger;
        private readonly CIABotOptions _options;
        private readonly ulong _adminId;

        public SlashCommandModule(IOptions<CIABotOptions> options, SettingsManager settingsManager, ILogger<SlashCommandModule> logger)
        {
            _settingsManager = settingsManager;
            _logger = logger;
            _options = options.Value;
            _adminId = _options.AdminId;
        }

        private bool CheckIfAuthorIsAdmin(SocketGuildUser user)
        {
            bool isMod = user.Roles.Any(role => role.Name.ToLower().Contains("mod"));
            bool canManageMessages = user.GuildPermissions.ManageMessages;
            bool isAdmin = user.GuildPermissions.Administrator;
            bool isBotOwner = user.Id == _adminId;

            return isMod || canManageMessages || isAdmin || isBotOwner;
        }

        private async Task<string> RunIfAuthorIsAdmin(SocketGuildUser user, Func<Task> function, string paramName, string? element = null)
        {
            if (CheckIfAuthorIsAdmin(user))
            {
                try
                {
                    await function();
                    return element != null ? $"{element} updated in parameter {paramName}" : $"Parameter {paramName} updated successfully";
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, $"Error updating {paramName}");
                    return $"Error updating {paramName}";
                }
            }
            else
            {
                _logger.LogInformation($"Insufficient permissions for {user.Username} (ID: {user.Id})");
                return "You don't have permission to do that.";
            }
        }

        [SlashCommand("bot-timeout", "Stops the bot from redacting messages for a while, between 5 minutes and 6 hours")]
        public async Task BotTimeout([Summary("duration", "The duration in minutes to stop redacting messages")] int duration)
        {
            var settings = _settingsManager.Settings;

            if (settings.TimeoutExpiration > DateTimeOffset.UtcNow.ToUnixTimeSeconds())
            {
                await RespondAsync("The bot is already in timeout.", ephemeral: true);
                return;
            }

            _logger.LogInformation($"Setting timeout for {duration} minutes.");
            settings.TimeoutExpiration = DateTimeOffset.UtcNow.ToUnixTimeSeconds() + (duration * 60);
            _settingsManager.SaveSettings();

            await RespondAsync($"Timed out for {duration} minutes", ephemeral: true);
        }

        [SlashCommand("show-values", "Shows the current configuration values")]
        public async Task ShowValues()
        {
            var settings = _settingsManager.Settings;
            var settingsJson = System.Text.Json.JsonSerializer.Serialize(settings, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
            _logger.LogInformation($"Showing configuration values.");
            await RespondAsync($"```json\n{settingsJson}\n```", ephemeral: true);
        }

        [SlashCommand("read-json", "Reloads the configuration values from persistence.json")]
        public async Task ReadJson()
        {
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.LoadSettings();
                _logger.LogInformation("Settings reloaded from persistence.json");
                return Task.CompletedTask;
            }, "settings");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("change-bypass-prefix", "Changes the prefix that allows bypassing the bot")]
        public async Task ChangeBypassPrefix(string newPrefix)
        {
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.ChangeConfigValue("BypassPrefix", newPrefix);
                _logger.LogInformation($"Bypass prefix changed to {newPrefix}");
                return Task.CompletedTask;
            }, "bypass_prefix");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("change-selected-chance", "Changes the chance to select any random message for redaction")]
        public async Task ChangeSelectedChance([Summary("new_chance", "The new threshold for redaction")] double newChance)
        {
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.ChangeConfigValue("SelectionChance", newChance / 100.0);
                _logger.LogInformation($"Selection chance changed to {newChance}%.");
                return Task.CompletedTask;
            }, "selection_chance");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("change-redacted-chance", "Changes the chance to redact any random word in a selected message")]
        public async Task ChangeRedactedChance([Summary("new_chance", "The new threshold for redacting words")] double newChance)
        {
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.ChangeConfigValue("RedactionChance", newChance / 100.0);
                _logger.LogInformation($"Redaction chance changed to {newChance}%.");
                return Task.CompletedTask;
            }, "redaction_chance");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("change-trigger-word-chance", "Changes the chance to redact a trigger word")]
        public async Task ChangeTriggerWordChance([Summary("new_chance", "The new threshold for trigger word redaction")] double newChance)
        {
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.ChangeConfigValue("TriggerWordChance", newChance / 100.0);
                _logger.LogInformation($"Trigger word chance changed to {newChance}%.");
                return Task.CompletedTask;
            }, "trigger_word_chance");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("add-channels-to-blacklist", "Adds a specified channel to the blacklist")]
        public async Task AddChannelsToBlacklist([Summary("new_channel_ids", "Comma-separated list of channel IDs to blacklist")] string newChannelIds)
        {
            var channelIdList = newChannelIds.Split(',').Select(id => id.Trim()).ToHashSet();
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.AddElementsToSet("ChannelBlacklist", channelIdList);
                _logger.LogInformation($"Added channels to blacklist: {string.Join(", ", channelIdList)}");
                return Task.CompletedTask;
            }, "channel_blacklist");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("remove-channels-from-blacklist", "Removes a specified channel from the blacklist")]
        public async Task RemoveChannelsFromBlacklist([Summary("old_channel_ids", "Comma-separated list of channel IDs to remove from blacklist")] string oldChannelIds)
        {
            var channelIdList = oldChannelIds.Split(',').Select(id => id.Trim()).ToHashSet();
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.RemoveElementsFromSet("ChannelBlacklist", channelIdList);
                _logger.LogInformation($"Removed channels from blacklist: {string.Join(", ", channelIdList)}");
                return Task.CompletedTask;
            }, "channel_blacklist");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("add-trigger-words", "Adds a trigger word to the list of words that trigger the bot")]
        public async Task AddTriggerWords([Summary("new_trigger_words", "Comma-separated list of trigger words to add")] string newTriggerWords)
        {
            var triggerWordList = newTriggerWords.Split(',').Select(word => word.Trim()).ToHashSet();
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.AddElementsToSet("TriggerWords", triggerWordList);
                _logger.LogInformation($"Added trigger words: {string.Join(", ", triggerWordList)}");
                return Task.CompletedTask;
            }, "trigger_words");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("remove-trigger-words", "Removes a trigger word from the list of words that trigger the bot")]
        public async Task RemoveTriggerWords([Summary("old_trigger_words", "Comma-separated list of trigger words to remove")] string oldTriggerWords)
        {
            var triggerWordList = oldTriggerWords.Split(',').Select(word => word.Trim()).ToHashSet();
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.RemoveElementsFromSet("TriggerWords", triggerWordList);
                _logger.LogInformation($"Removed trigger words: {string.Join(", ", triggerWordList)}");
                return Task.CompletedTask;
            }, "trigger_words");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("change-debug-channel-id", "Changes debug channel ID")]
        public async Task ChangeDebugChannelId([Summary("channel_id", "The new debug channel ID")] string channelId)
        {
            var result = await RunIfAuthorIsAdmin(Context.User as SocketGuildUser, () => {
                _settingsManager.ChangeConfigValue("DebugChannelId", channelId);
                _logger.LogInformation($"Debug channel ID changed to {channelId}");
                return Task.CompletedTask;
            }, "debug_channel_id");

            await RespondAsync(result, ephemeral: true);
        }

        [SlashCommand("help", "Shows the help message")]
        public async Task Help()
        {
            _logger.LogInformation($"Showing help message.");
            await RespondAsync($"Bypassing the bot:\nType `{_settingsManager.Settings.BypassPrefix}` before a message to bypass the bot.\nExample:\n`{_settingsManager.Settings.BypassPrefix}help I’m being killed by a paramilitary group`\nAvailable commands:\n`/change-selected-chance`, `/change-redacted-chance`, `/change-trigger-word-chance`, `/show-values`, `/add-channels-to-blacklist`, `/remove-channels-from-blacklist`, `/add-trigger-word`, `/remove-trigger-word`, `/help`", ephemeral: true);
        }
    }
}
