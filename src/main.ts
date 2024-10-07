import Config from "@src/core/Config";
import { Client } from "discordx";
import { importx } from "@discordx/importer";
import { ChannelType, IntentsBitField, Partials, Activity, ActivityType } from "discord.js";

const logger = require("@src/utils/Logger").Logger.logger

export abstract class Main {
    private static _client: Client;

    static get Client(): Client {
        return this._client;
    }

    static preflight() {
        Config.loadEnv();
        if (Config.logDestination === "datadog") {
            Config.datadogLogTrail();
        }
    }

    static async start(): Promise<void> {
        this._client = new Client({
            botId: Config.botAppID,
            intents: [
                IntentsBitField.Flags.Guilds,
                IntentsBitField.Flags.GuildMessagePolls,
                IntentsBitField.Flags.GuildMembers
            ],
            silent: false,
        })

        this._client.on("ready", async () => {
            await this._client.initApplicationCommands();

            this._client.user?.setActivity("Listening for codewords", {type: ActivityType.Custom})
            logger.info(`Loggied in as ${this._client.user?.tag}}`)
        }) 

        this._client.on("interactionCreate", (interaction) => {
            this._client.executeInteraction(interaction)
        })

        await importx(`${__dirname}/commands/**/*.{js, ts}`);
        await this._client.login(Config.botToken).then(r => Promise);
    }
}

Main.preflight()
Main.start()