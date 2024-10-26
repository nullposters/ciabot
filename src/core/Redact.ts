import { ArgsOf, Client, Discord, On } from "discordx";
import Config from "@src/utils/Config";

@Discord()
export class Redact {
    @On({event: "messageCreate"})
    async onMessage(
        [message]: ArgsOf<"messageCreate">,
        client: Client,
        guardPayload: any
    ) {
        const isBot = message?.author?.id == Config.botAppID;
        const hasBypassChar = message?.content?.startsWith(Config.botBypassChar);
        if (isBot || hasBypassChar)
            return;

        const words = message.content.split(" ");
        const hasTriggerWord = Config.botTriggerWords.some((triggerWord: string): boolean => 
            words.some(word => word.toLowerCase() === triggerWord.toLowerCase())
        );

        if (hasTriggerWord) {
            await this.handleTriggerWord(message);
        } else if (Math.random() < Config.botRedactChance) {
            await this.handleRandomChance(message)
        }
    }
    
    private async handleTriggerWord(message: any) {
        // TODO: implement handling of trigger words
    }

    private async handleRandomChance(message: any) {
        // TODO: implement random redaction chance
    }
}