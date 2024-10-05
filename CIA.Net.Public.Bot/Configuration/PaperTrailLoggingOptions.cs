using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CIA.Net.Public.Bot.Configuration
{
    internal class PaperTrailLoggingOptions
    {
        public static string SettingsName => "PaperTrailLogging";
        public string Destination { get; set; } = "localhost";
        public int Port { get; set; } = 514;
    }
}
