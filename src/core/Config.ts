import fs from 'fs';
import path from 'path';
import { forceExit, ConfigError } from "@src/core/Error"
import { Logger } from "@src/utils/Logger"

export default abstract class Config {
    static botToken: string;
    static botAppID: string;
    static botAdminID: string;
    static botGuildID: string;
    static logDestination: string;
    static ddApiKey: string;
    static ddHostname: string;
    static ddService: string;
    static ddSource: string;
    static ddTags: string


    static loadEnv(): void {

        const requiredEnvVars = ['CIABOT_TOKEN', 'CIABOT_APPID', 'CIABOT_ADMIN_ID', 'CIABOT_GUILD_ID']

        const envVarMapping: {[key: string]: string} = {
            'CIABOT_TOKEN': 'botToken',
            'CIABOT_APPID': 'botAppID',
            'CIABOT_ADMIN_ID': 'botAdminID',
            'CIABOT_GUILD_ID': 'botGuildID'
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
        const requiredEnvVars = ['DD_APIKEY', 'DD_HOSTNAME', 'DD_SERVICE', 'DD_TAGS']

        const envVarMapping: {[key: string]: string} = {
            'DD_APIKEY': 'ddApiKey',
            'DD_HOSTNAME': 'ddHostname',
            'DD_SERVICE': 'ddService',
            'DD_TAGS': 'ddTags'
        };

        for (const envVar of requiredEnvVars) {
            if (!process.env[envVar]) {
                forceExit(new ConfigError(`Missing required environment variable ${envVar}`).toString());
            } else {
                // @ts-expect-error already checked for the values, compiler is stupid
                this[envVarMapping[envVar]] = process.env[envVar]!;
            }
        }

        Logger.initDatadogTransport();
        
    }
}