const { Client, GatewayIntentBits } = require("discord.js");
const fs = require('fs');
const createLogger = require('logging').default
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ],
});

require('dotenv').config();

const secret = process.env.SECRET;
const adminId = process.env.ADMIN_ID;
const ciaBotId = process.env.CIABOT_ID;
const errorChannelId = process.env.error_channel_id;

let persistenceData = JSON.parse(fs.readFileSync('./persistence.json', 'utf8'));
let redactionChance = persistenceData.redactionChance || 0.08;
let chance = persistenceData.chance || 0.005;
let triggerWords = persistenceData.triggerWords || [];
let triggerWordChance = persistenceData.triggerWordChance || 0.1;
const logger = createLogger('CIA Logger');
logger.info(secret)

client.login(secret);

client.once("ready", () => {
    logger.info(`Logged in as ${client.user.displayName}!`);
});


client.on("messageCreate", async (message) => {
    const isCiaBot = message?.author?.id == ciaBotId;
    const hasBypassCharacter = message?.content?.startsWith(">>");
    if (isCiaBot || hasBypassCharacter) return;
    if (message.attachments.size > 0) {
        const hasImage = message.attachments.some(attachment => {
            return attachment.contentType && attachment.contentType.startsWith('image/');
        });
        if (hasImage) return;
    }

    const isCommand = message?.content?.startsWith('!') || false;
    if (isCommand) {
        handleCommand(message);
        return;
    }

    const isCiaBroadcast = message?.content?.startsWith("$>") || false;
    if (isCiaBroadcast) {
        handleBroadcastFromCiaCommand(message, message?.content.split('').splice(2).join(''));
        return;
    }

    const words = message.content.split(' ');
    const containsTriggerWord = triggerWords.some(triggerWord =>
        words.some(word => word.toLowerCase() === triggerWord.toLowerCase())
    );

    if (containsTriggerWord) await handleTriggerWord(message)
    else if (Math.random() < chance) await handleRandomChance(message)
});

async function handleTriggerWord(message) {
    let messageArr = message.content.split(' ');
    let lastTriggerWordIndex = -1;
    let result = {};

    if (messageArr.length === 1) {
        result = handleTriggerRedaction(messageArr, 0);
    } else {
        for (let i = 0; i < messageArr.length; i++) {
            result = handleTriggerRedaction(messageArr, i, lastTriggerWordIndex);
        }

        if (!result.triggerWordRedacted && lastTriggerWordIndex !== -1) {
            result.messageArr[lastTriggerWordIndex] = '`[REDACTED]`';
            result.triggerWordRedacted = true;
        }
    }

    if (result.triggerWordRedacted) {
        const createdMessage = result.messageArr.join(' ');

        try {
            const userName = message?.member?.displayName || "Things got weird so this is the username for this message, yell at piff for this transgression";
            await message.delete();
            await message.channel.send(`${userName}:\n${createdMessage}`);
        } catch (error) {
            logger.error("Failed to delete or send a message:", error);
        }
    }
}

function handleTriggerRedaction(messageArr, idx, lastTriggerWordIndex) {
    let triggerWordRedacted = false;
    const lowerCaseWord = messageArr[idx].toLowerCase();

    if (triggerWords.includes(lowerCaseWord)) {
        if (lastTriggerWordIndex)
            lastTriggerWordIndex = idx;
        if (Math.random() < triggerWordChance) {
            messageArr[idx] = '`[REDACTED]`';
            triggerWordRedacted = true;
        }
    }

    return { messageArr: messageArr, triggerWordRedacted: triggerWordRedacted }
}

async function handleRandomChance(message) {
    const userName = message.member.displayName;
    const messageArr = message.content.split(' ');
    let wordReplaced = false;

    for (let i = 0; i < messageArr.length; i++) {
        if (Math.random() < redactionChance) {
            messageArr[i] = '`[REDACTED]`';
            wordReplaced = true;
        }
    }

    if (!wordReplaced && messageArr.length > 0) {
        const randomIndex = Math.floor(Math.random() * messageArr.length);
        messageArr[randomIndex] = '`[REDACTED]`';
        wordReplaced = true;
    }

    if (wordReplaced) {
        const createdMessage = messageArr.join(' ');

        try {
            await message.delete();
            await message.channel.send(`${userName}: ${createdMessage}`);
        } catch (error) {
            logger.error("Failed to delete or send a message:", error);
        }
    }
}

function handleCommand(message) {
    logger.info('Command attempted')
    const isBotAdministratorOrModerator = message?.member?.roles?.cache?.some(role => role.name === 'mod') || false;
    const isAdministrator = message?.author?.id == adminId || false;

    if (isAdministrator || isBotAdministratorOrModerator) {
        logger.info(`${isAdministrator ? 'Admin' : 'User ' + message.member.displayName + ' '} attempted to run command ${message.content.split(' ')}`)
        const [command, ...args] = message.content.split(' ');
        let isMultiWordArgument = false;
        let combinedMultiWordArg = "";
        if (args[0]?.startsWith("\"") && args[args.length - 1]?.endsWith("\"")) {
            for (let i = 0; i < args.length; i++) {
                combinedMultiWordArg += args[i] + " ";
            }
            combinedMultiWordArg = combinedMultiWordArg.replace(/\"/g, '').trimEnd();;
            isMultiWordArgument = true;
        }
        const arg = isMultiWordArgument ? combinedMultiWordArg : args[0]

        switch (command.toLowerCase()) {
            case '!changeredacted':
                logger.info(`Changing redaction chance to ${args[0]}`)
                handleNumberCommand(args[0], 'redact a word', (value) => {
                    redactionChance = value;
                    updatePersistenceFile();
                }, message);
                break;
            case '!changechance':
                logger.info(`Changing total chance to ${args[0]}`)
                handleNumberCommand(args[0], 'replace words', (value) => {
                    chance = value;
                    updatePersistenceFile();
                }, message);
                break;
            case '!readjson':
                logger.info(`Reading JSON persistence file`)
                handleReadJsonCommand(message);
                break;
            case '!help':
                logger.info(`Sending help message`)
                sendHelpMessage(message);
                break;
            case '!checkvalues':
                logger.info(`Sending current values`)
                checkValues(message);
                break;
            case '!addtriggerword':
                logger.info("Adding trigger word to dictionary");
                addTriggerWordToDictionary(message, arg);
                break;
            case '!rmtriggerword':
                logger.info("Removing trigger word from dictionary");
                removeTriggerWordFromDictionary(message, arg);
                break;
            case '!changetriggerwordchance':
                logger.info(`Changing chance a trigger word triggers a redaction to ${args[0]}`)
                handleNumberCommand(args[0], 'set off redactions from trigger words', (value) => {
                    triggerWordChance = value;
                    updatePersistenceFile();
                }, message);
                break;
            default:
                logger.warn(`Unknown command encountered`)
                message.channel.send('Unknown command. Type !help for help message.');
        }
    } else {
        logger.warn(`Unauthorized user ${message.member.displayName} attempted to run a command.`)
    }
    return;
}

function addTriggerWordToDictionary(message, triggerWord) {
    if (triggerWord && triggerWord.length > 0) {
        const triggerAlreadyPresent = triggerWords.find(c => c.toLowerCase() == triggerWord.toLowerCase())
        if (!triggerAlreadyPresent) {
            triggerWords.push(triggerWord);
            updatePersistenceFile();
            message.channel.send(`Added '${triggerWord}' to dictionary.`);
        } else {
            logger.info(`Word ${triggerWord} already present in dictionary`);
            message.channel.send(`Word '${triggerWord}'already present in dictionary`);
        }
    } else {
        logger.error("No word found to add to dictionary");
        message.channel.send("No word found to add to dictionary, try !addTriggerWord word");
    }
}

function removeTriggerWordFromDictionary(message, triggerWord) {
    if (triggerWord && triggerWord.length > 0) {
        let wordToRemove = triggerWords.findIndex(c => c.toLowerCase() == triggerWord.toLowerCase());
        if (wordToRemove >= 0) {
            triggerWords.splice(wordToRemove);
            updatePersistenceFile();
            message.channel.send(`Removed '${triggerWord}' from dictionary.`);
        } else {
            logger.info(`Word ${triggerWord} was not found in dictionary`);
            message.channel.send(`Word '${triggerWord}' was not found in dictionary`);
        }
    } else {
        logger.error("No word found to remove from dictionary");
        message.channel.send("No word found to remove from dictionary, try !rmTriggerWord word");
    }
}

function handleNumberCommand(value, description, updateFunction, message) {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
        const probabilityValue = (numValue / 100);
        updateFunction(probabilityValue);
        message.channel.send(`Chance to ${description} updated to ${numValue}%`);
    } else {
        logger.warn('Could not parse float')
        message.channel.send('Please provide a valid number for the command.');
    }
}

function handleReadJsonCommand(message) {
    try {
        const json = JSON.parse(fs.readFileSync('./persistence.json', 'utf8'));
        message.channel.send(JSON.stringify(json, null, 2).substring(0, 1995) + '...'); // arbitrary number under 2000 because discord limit
    } catch (error) {
        logger.error("Failed to read JSON file:", error);
        message.channel.send('Failed to read the JSON file.');
    }
}

function updatePersistenceFile() {
    logger.info('Updating json file');
    const data = {
        redactionChance: redactionChance,
        chance: chance,
        triggerWordChance: triggerWordChance,
        triggerWords: triggerWords,
    };

    fs.writeFileSync('./persistence.json', JSON.stringify(data, null, 2), 'utf8', (err) => {
        if (err) {
            logger.error("Error writing to JSON file:", err);
        }
    });
}

function sendHelpMessage(message) {
    const helpMessage = `
Bypassing the bot:
Type \`>>\` before a message to bypass the bot for important messages or if it's being super annoying.
Example:
\`>>help I’m being killed by a paramilitary group\`

Available commands:

\`!changeRedacted <value>\`: Chance using a decimal percentage value to replace a word in a message with \`[REDACTED]\`.
\`!changeChance <value>\`: Chance using a decimal percentage value to trigger word replacements or redactions in a message. This is the overall chance the CIA bot has to change your message, the other value for redacted chance is used to determine how that message is changed.
\`!changeTriggerWordChance <value>\`: Chance using a decimal percentage value to redact words that are considered 'trigger words'. If a trigger word is present in the message, this is the chance that word will be \`[REDACTED]\`
\`!checkValues\`: Responds with the current configuration.
\`!addTriggerWord <value>\`: Adds a new trigger word to the dictionary.
\`!rmTriggerWord <value>\`: Removes a trigger word from the dictionary if present.
\`!help\`: Lists all available commands with their descriptions, along with some tips.
    `;
    message.channel.send(helpMessage);
}

function checkValues(message) {
    try {
        const json = JSON.parse(fs.readFileSync('./persistence.json', 'utf8'));
        const response = `
\`Overall chance to have a message modified\`: ${(json.chance * 100).toFixed(2)}%.
\`Chance to change a word to [REDACTED]\`: ${(json.redactionChance * 100).toFixed(2)}%.
\`Chance to redact a trigger word if one is found in the message\`: ${(json.triggerWordChance * 100).toFixed(2)}%.
    `;
        message.channel.send(response);

    } catch (error) {
        logger.error("Failed to read JSON file:", error);
        message.channel.send('Failed to read the JSON file.');
    }
}

async function sendErrorMessage(message) {
    try {
        const channel = await client.channels.fetch(errorChannelId);
        if (channel) {
            await channel.send(message);
        } else {
            logger.error('Error log channel not found or is not a text channel.');
        }
    } catch (error) {
        logger.error('Failed to send error message:', error);
    }
}

process.on('unhandledRejection', async (reason, promise) => {
    logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
    await sendErrorMessage(`Unhandled promise rejection:\n${reason}`)
});

process.on('uncaughtException', async (error) => {
    console.error('Uncaught Exception thrown:', error);
    await sendErrorMessage(`Unhandled exception\n${error}`);
});