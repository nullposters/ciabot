namespace CIA.Net.Public.Bot
{
    using CIA.Net.Public.Bot.Configuration;
    using Microsoft.Extensions.Options;
    using Newtonsoft.Json;
    using System.IO;

    public class SettingsManager
    {
        private readonly IOptions<BotConfiguration> _options;
        private readonly BotConfiguration _settings;
        private const string SettingsFilePath = "settings.json";

        public SettingsManager(IOptions<BotConfiguration> options)
        {
            _options = options;
            _settings = _options.Value;

            LoadSettings();
        }

        public BotConfiguration Settings => _settings;

        public void LoadSettings()
        {
            if (File.Exists(SettingsFilePath))
            {
                var settingsJson = File.ReadAllText(SettingsFilePath);
                JsonConvert.PopulateObject(settingsJson, _settings);
            }
        }

        public void SaveSettings()
        {
            var settingsJson = JsonConvert.SerializeObject(_settings, Formatting.Indented);
            File.WriteAllText(SettingsFilePath, settingsJson);
        }

        public void ChangeConfigValue(string configKey, object newValue)
        {
            typeof(BotConfiguration).GetProperty(configKey)?.SetValue(_settings, newValue);
            SaveSettings();
        }

        public void AddElementsToSet(string configKey, HashSet<string> newElements)
        {
            var set = typeof(BotConfiguration).GetProperty(configKey)?.GetValue(_settings) as HashSet<string>;
            if (set != null)
            {
                set.UnionWith(newElements);
                SaveSettings();
            }
        }

        public void RemoveElementsFromSet(string configKey, HashSet<string> elementsToRemove)
        {
            var set = typeof(BotConfiguration).GetProperty(configKey)?.GetValue(_settings) as HashSet<string>;
            if (set != null)
            {
                set.ExceptWith(elementsToRemove);
                SaveSettings();
            }
        }
    }

}
