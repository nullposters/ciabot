
namespace CIA.Net.Public.Bot.Configuration
{
    public class BotConfigurationOptions
    {
        public static string SettingsName => "BotConfiguration";
        public double RedactionChance { get; set; } = 0.08;
        public double SelectionChance { get; set; } = 0.005;
        public HashSet<string> TriggerWords { get; set; } = [];
        public double TriggerWordChance { get; set; } = 0.1;
        public string BypassPrefix { get; set; } = ">>";
        public HashSet<string> ChannelBlacklist { get; set; } = [];
        public HashSet<string> ChannelWhitelist { get; set; } = [];
        public long TimeoutExpiration { get; set; } = 0;
        public long DebugChannelId { get; set; }
    }
}
