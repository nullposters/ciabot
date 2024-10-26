import type { CommandInteraction, GuildMember, User } from "discord.js";
import { ApplicationCommandOptionType, EmbedBuilder, Client } from "discord.js";
import { Discord, Slash, SlashGroup, SlashOption } from "discordx";

@Discord()
export abstract class About {
    @Slash({description: "Displays bot's about info", name: "about"})
    async about(
        interaction: CommandInteraction
    ) {
        const embed = new EmbedBuilder()
        .setColor(0x0099FF)
        .setTitle("About CIAbot")
        .setAuthor({name: "ɴᴜʟʟposters, inc.", iconURL: "https://avatars.githubusercontent.com/u/183155718", url: "https://github.com/nullposters/ciabot"})
        .setDescription("This is a dockerized TypeScript project that uses the discord.js and discordx libraries to run the glowiest bot in all of Discord. It'll randomly redact your messages, react to messages, ~~and prop up based puppet dictators in South American countries~~.")

        await interaction.reply({embeds: [embed]})
    }
    
}