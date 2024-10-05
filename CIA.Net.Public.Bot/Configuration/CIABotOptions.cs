namespace CIA.Net.Public.Bot.Configuration
{
    public class CIABotOptions
    {
        public static string SettingsName => "CIABotOptions";
        public string Token { get; set; } = string.Empty;
        public string SettingsPath { get; set; } = string.Empty;
        public ulong AdminId { get; set; }
        public ulong GuildId { get; set; }
        public string PostgresDb { get; set; } = string.Empty;
        public string PostgresUser { get; set; } = string.Empty;
        public string PostgresPassword { get; set; } = string.Empty;
        public string PostgresHost { get; set; } = string.Empty;
        public bool IsProduction { get; set; }
        public ulong DebugChannelId { get; set; }
    }
}
