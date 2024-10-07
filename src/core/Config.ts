import fs from 'fs';
import path from 'path';
import { forceExit, ConfigError } from "@src/core/Error"
import { Logger } from "@src/utils/Logger"

require('dotenv').config()


export default abstract class Config {
    static botToken: string;
    static botAppID: string;
    static botAdminID: string;
    static botGuildID: string;
    static botSettingsPath: string;
    static botSettings: object;

    static logDestination: string;
    
    static ddApiKey: string;
    static ddHostname: string;
    static ddService: string;
    static ddSource: string;
    static ddTags: string;
    static ddRegion: string;

    static loadEnv(): void {

        const requiredEnvVars = ['CIABOT_TOKEN', 'CIABOT_APPID', 'CIABOT_ADMIN_ID', 'CIABOT_GUILD_ID', 'CIABOT_SETTINGS_PATH']

        const envVarMapping: {[key: string]: string} = {
            'CIABOT_TOKEN': 'botToken',
            'CIABOT_APPID': 'botAppID',
            'CIABOT_ADMIN_ID': 'botAdminID',
            'CIABOT_GUILD_ID': 'botGuildID',
            'CIABOT_SETTINGS_PATH': 'botSettingsPath'
        };

        for (const envVar of requiredEnvVars) {
            if (!process.env[envVar]) {
                forceExit(new ConfigError(`Missing required environment variable ${envVar}`).toString());
            } else {
                // @ts-expect-error already checked for the values, compiler is stupid
                this[envVarMapping[envVar]] = process.env[envVar]!;
            }
        }
        
    }

    static datadogLogTrail(): void {
        if (!process.env.DD_APIKEY) {
            Logger.logger.error("Log destination set to DataDog, but no API key was provided!")
            forceExit(new ConfigError("Missing required environment variable 'DD_APIKEY'!").toString());
        }

        const optionalEnvVars = ['DD_HOSTNAME', 'DD_SERVICE', 'DD_TAGS', 'DD_REGION']
        const envVarMapping: {[key: string]: string} = {
            'DD_HOSTNAME': 'ddHostname',
            'DD_SERVICE': 'ddService',
            'DD_TAGS': 'ddTags',
            'DD_REGION': 'ddRegion'
        };

        for (const envVar of optionalEnvVars) {
            if (process.env[envVar]) {
                // @ts-expect-error already checked for the values, compiler is stupid
                this[envVarMapping[envVar]] = process.env[envVar]!;
            } else {
                Logger.logger.warn(`No value found for ${envVar}`)
            }
        }
        Logger.initDatadogTransport();   
    }

    static loadSettings(): void {
        const settingsPath = path.join(this.botSettingsPath, "settings.json");

        if (!fs.existsSync(settingsPath)) {
            Logger.logger.warn(`Settings file not found at ${settingsPath}, creating with default values.`);
            const defaultSettings = {
                // Add your default settings here
                redactionChance: 0.08,
                selectionChance: 0.005,
                triggerWords: [],
                triggerWordChance: 0.1,
                bypassPrefix: ">>",
                channelBlacklist: [],
                channelWhiteList: [],
                timeoutExpiration: 0
            };
            fs.writeFileSync(settingsPath, JSON.stringify(defaultSettings, null, 2));
            this.botSettings = defaultSettings;
            Logger.logger.debug(`Populated settings.json with the default values: \n${JSON.stringify(this.botSettings)}`)
        } else {
            Logger.logger.info(`Loading settings from ${settingsPath}`);
            const settingsData = fs.readFileSync(settingsPath, 'utf-8');
            this.botSettings = JSON.parse(settingsData);
            Logger.logger.debug(`Loaded settings: \n${JSON.stringify(this.botSettings)}`)
        }
    }
}