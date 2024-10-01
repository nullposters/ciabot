import os
import socket
import random
import string
import logging
import discord
import jsonpickle
from typing import Any
from datetime import datetime
from dotenv import load_dotenv
from unicodedata import lookup
from discord import app_commands
from collections.abc import Callable
from logging.handlers import SysLogHandler


load_dotenv()


# Logging initialization
class ContextFilter(logging.Filter):
    hostname: str = socket.gethostname()
    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True
    
syslog_url = os.getenv('PAPERTRAIL_LOG_DESTINATION', os.getenv('LOG_DESTINATION', 'localhost')) # Backwards compatible with the original papertrail setup
syslog_port = int(os.getenv('PAPERTRAIL_LOG_PORT', os.getenv('LOG_PORT', 514))) # Backwards compatible with the original papertrail setup
syslogaddress = (syslog_url, syslog_port)
syslog = SysLogHandler(address=syslogaddress, facility=SysLogHandler.LOG_USER)
syslog.addFilter(ContextFilter())
format = '%(asctime)s %(hostname)s cia_bot: %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(syslog)
logger.setLevel(logging.INFO)
# End logging initialization


token = os.getenv('CIABOT_SECRET', os.getenv('CIABOT_TOKEN')) # Backwards compatible with the original token name
admin_id = os.getenv('CIABOT_ADMIN_ID')
settings_path = os.getenv('CIABOT_SETTINGS_PATH', 'settings.json')
test_guild = discord.Object(os.getenv('CIABOT_GUILD_ID'))


def save_settings() -> None:
    """Saves the current settings to the settings.json file"""
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(jsonpickle.encode(settings))


def load_settings() -> dict[str, float | set[str]]:
    """Loads the settings from the settings.json file"""
    default_settings = {
        'redaction_chance': 0.08,
        'selection_chance': 0.005,
        'trigger_words': set(),
        'trigger_word_chance': 0.1,
        'bypass_prefix': '>>',
        'channel_blacklist': set(),
        'timeout_expiration': 0,
    }
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = jsonpickle.decode(f.read())
            for key, _ in default_settings.items():
                if key not in settings:
                    settings[key] = default_settings[key]
            return settings
    else:
        return default_settings


settings = load_settings()
save_settings()


REDACTION = [
    "`[REDACTED]`",
    "`[EXPUNGED]`",
    "`[CLASSIFIED]`",
    "`[REDACTED BY CIA]`",
    "`[REDACTED BY FBI]`",
    "`[REDACTED BY NSA]`",
    "`[REDACTED BY DHS]`",
    "`[REDACTED BY MI6]`",
    "`[REDACTED BY KGB]`",
    "`********`",
    "`████████"
]

JSBAD = "bad"


class CiaBotClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # Here we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        if test_guild:
            # This copies the global commands over to your guild.
            self.tree.copy_global_to(guild=test_guild)
            await self.tree.sync(guild=test_guild)


intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
client = CiaBotClient(intents=intents)


def extract_message_metadata(message: discord.Message) -> tuple:
    """Extracts the message ID and author name from a discord.Message object"""
    message_id = message.id
    message_author = message.author.name
    return message_id, message_author


def redact_message(message: discord.Message, trigger_word_indices: list[int]) -> str:
    """Redacts a given message. If the message contains trigger words, redacts any word at random from the trigger words. Otherwise, redacts any random word from the message."""
    message_id, message_author = extract_message_metadata(message)
    logging.info(f"Processing message {message_id=}, {message_author=}, {'has trigger word' if trigger_word_indices else 'randomly selected'}")
    message_content = message.content.split(' ')
    was_redacted = False
    indices = trigger_word_indices if trigger_word_indices else range(len(message_content))
    threshold = settings['trigger_word_chance'] if trigger_word_indices else settings['redaction_chance']
    for idx in indices:
        if random.random() < threshold:
            message_content[idx] = random.choice(REDACTION)
            was_redacted = True
    if not was_redacted:
        random_index = random.choice(indices)
        message_content[random_index] = random.choice(REDACTION)
    return ' '.join(message_content)


def check_if_author_is_admin(interaction: discord.Interaction) -> bool:
    """Checks if the user is an admin or mod"""
    is_mod = any("mod" in role.name or "Mod" in role.name for role in interaction.user.roles)
    can_manage_messages = interaction.user.top_role.permissions.manage_messages
    is_admin = interaction.user.top_role.permissions.administrator
    is_bot_owner = interaction.user.id == int(admin_id)
    return is_mod or can_manage_messages or is_admin or is_bot_owner


def run_if_author_is_admin(interaction: discord.Interaction, function: Callable[[str, float], None], param_name: str, element: str = None) -> str:
    """Runs a function if the user is an admin or mod"""
    if check_if_author_is_admin(interaction):
        try:
            function()
            if element:
                return f"{element} updated in parameter {param_name}"
            else:
                return f"Parameter {param_name} updated successfully"
        except Exception as e:
            logger.error(f"Error updating {param_name}: {e}")
            return f"Error updating {param_name}"
    else:
        logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Insufficient permissions")
        return "You don't have permission to do that"


def change_config_value(interaction: discord.Interaction, config_key: str, new_value: Any) -> None:
    """Changes a configuration value in the settings dictionary"""
    logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Changing config value {config_key} to {new_value}")
    settings[config_key] = new_value
    save_settings()


def add_elements_to_set(interaction: discord.Interaction, config_key: str, new_elements: set[Any]) -> None:
    """Adds one or more elements to a set in the settings dictionary. The elements must be wrapped in a set, even if there is only one element."""
    logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Adding elements {new_elements} to {config_key}")
    settings[config_key].update(new_elements)
    save_settings()


def remove_elements_from_set(interaction: discord.Interaction, config_key: str, old_elements: set[Any]) -> None:
    """Removes one or more elements from a set in the settings dictionary. The elements must be wrapped in a set, even if there is only one element."""
    logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Removing elements {old_elements} from {config_key}")
    settings[config_key].difference_update(old_elements)
    save_settings()


async def react_with_funny_letters(message: discord.Message, text: string):
    """Reacts to a message with single-letter emojis. The string to emulate is deduplicated before reacting."""
    upper_text = text.upper()
    letter_set = set(upper_text)
    if any(c not in set(string.ascii_uppercase) for c in letter_set):
        return
    for char in upper_text:
        await message.add_reaction(lookup(f'REGIONAL INDICATOR SYMBOL LETTER {char}'))


@client.tree.command(
    name="bot-timeout",
    description="Stops the bot from redacting messages for a while, between 5 minutes and 6 hours"
)
@app_commands.describe(duration='The duration in minutes to stop redacting messages, between 5 and 360')
async def bot_timeout(interaction: discord.Interaction, duration: app_commands.Range[int, 5, 360]):
    if settings['timeout_expiration'] and datetime.now().timestamp() < settings['timeout_expiration']:
        await interaction.response.send_message("The bot is already in timeout.", ephemeral=True)
        return
    logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Timeout for {duration*60} seconds")
    settings['timeout_expiration'] = datetime.now().timestamp() + (duration*60)
    save_settings()
    await interaction.response.send_message(f"Timed out for {duration} minutes")

@client.tree.command(
    name="show-values",
    description="Shows the current configuration values"
)
async def show_values(interaction: discord.Interaction):
    logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Showing configuration values")
    await interaction.response.send_message(f"```json\n{jsonpickle.encode(settings, indent=2)}\n```", ephemeral=True)


@client.tree.command(
    name="read-json",
    description="Reloads the configuration values from persistence.json"
)
async def read_json(interaction: discord.Interaction):
    def logic():
        logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Reading configuration values from persistence.json")
        globals()['settings'] = load_settings()
    message = run_if_author_is_admin(interaction, logic, 'settings')
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="change-bypass-prefix",
    description="Changes the prefix that allows bypassing the bot"
)
@app_commands.describe(new_prefix='The new prefix to bypass the bot')
async def change_bypass_prefix(interaction: discord.Interaction, new_prefix: str):    
    message = run_if_author_is_admin(interaction, lambda: change_config_value(interaction, 'bypass_prefix', new_prefix), 'bypass_prefix')
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="change-selected-chance",
    description="Changes the chance to select any random message for redaction"
)
@app_commands.describe(new_chance='From 0 to 100, the new threshold of the selection check that will be applied to all messages for possible redaction.')
async def change_chance(interaction: discord.Interaction, new_chance: app_commands.Range[float, 0.0, 100.0]):
    message = run_if_author_is_admin(interaction, lambda: change_config_value(interaction, 'selection_chance', new_chance/100.0), 'selection_chance')
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="change-redacted-chance",
    description="Changes the chance to redact any random word in a selected message"
)
@app_commands.describe(new_chance='From 0 to 100, the new threshold of the redaction check that will be applied to all the words in a selected message. If all words pass the check, one random word will be redacted.')
async def change_redacted(interaction: discord.Interaction, new_chance: app_commands.Range[float, 0.0, 100.0]):
    message = run_if_author_is_admin(interaction, lambda: change_config_value(interaction, 'redaction_chance', new_chance/100.0), 'redaction_chance')
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="change-trigger-word-chance",
    description="Changes the chance to redact a trigger word"
)
@app_commands.describe(new_chance='From 0 to 100, the new threshold of the redaction check that will be applied to all the trigger words of any message. If all words pass the check, one random trigger word will be redacted.')
async def change_trigger_word_chance(interaction: discord.Interaction, new_chance: app_commands.Range[float, 0.0, 100.0]):
    message = run_if_author_is_admin(interaction, lambda: change_config_value(interaction, 'trigger_word_chance', new_chance/100.0), 'trigger_word_chance')
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="add-channels-to-blacklist",
    description="Adds a specified channel to the blacklist"
)
@app_commands.describe(new_channel_ids='The channel ID to add to the blacklist. Multiple channels can be added by separating them with a space.')
async def add_channel_to_blacklists(interaction: discord.Interaction, new_channel_ids: str):
    message = run_if_author_is_admin(interaction, lambda: add_elements_to_set(interaction, 'channel_blacklist', {channel_id.strip() for channel_id in new_channel_ids.split(' ')}), 'channel_blacklist', new_channel_ids)
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="remove-channels-from-blacklist",
    description="Removes a specified channel to the blacklist"
)
@app_commands.describe(old_channel_ids='The channel ID to remove from the blacklist. Multiple channels can be removed by separating them with a space.')
async def remove_channel_from_blacklists(interaction: discord.Interaction, old_channel_ids: str):
    message = run_if_author_is_admin(interaction, lambda: remove_elements_from_set(interaction, 'channel_blacklist', {channel_id.strip() for channel_id in old_channel_ids.split(' ')}), 'channel_blacklist', old_channel_ids)
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="add-trigger-words",
    description="Adds a trigger word to the list of words that trigger the bot"
)
@app_commands.describe(new_trigger_words='The new trigger word to add to the list. Multiple trigger words can be added by separating them with a space.')
async def add_trigger_words(interaction: discord.Interaction, new_trigger_words: str):
    message = run_if_author_is_admin(interaction, lambda: add_elements_to_set(interaction, 'trigger_words', {word.strip() for word in new_trigger_words.split(' ')}), 'trigger_words', new_trigger_words)
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="remove-trigger-words",
    description="Removes a trigger word from the list of words that trigger the bot"
)
@app_commands.describe(old_trigger_words='The trigger word to remove from the list. Multiple trigger words can be removed by separating them with a space.')
async def remove_trigger_words(interaction: discord.Interaction, old_trigger_words: str):
    message = run_if_author_is_admin(interaction, lambda: remove_elements_from_set(interaction, 'trigger_words', {word.strip() for word in old_trigger_words.split(' ')}), 'trigger_words', old_trigger_words)
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="help",
    description="Shows the help message"
)
async def help(interaction: discord.Interaction):
    logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Showing help message")
    await interaction.response.send_message(f"""Bypassing the bot:
Type `{settings['bypass_prefix']}` before a message to bypass the bot for important messages or if it's being super annoying.
Example:
`{settings['bypass_prefix']}help I’m being killed by a paramilitary group`

Available commands:
`/change-selected-chance <value>`: Chance (in percentage) to trigger word replacements or redactions in a message. This is the overall chance the CIA bot has to change your message, the other value for redacted chance is used to determine how that message is changed.
`/change-redacted-chance <value>`: Chance (in percentage) to replace a word in a message with `[REDACTED]`. If no word is replaced, one word will be chosen randomly and replaced.
`/change-trigger-word-chance <value>`: Chance (in percentage) to redact words that are considered 'trigger words'. If a trigger word is present in the message, this is the chance that any given word will be `[REDACTED]`. If no word is replaced, one trigger word will be chosen randomly and replaced.
`/show-values`: Responds with the current configuration.
`/add-channel-to-blacklist <value>`: Adds a channel ID to the channel blacklist
`/remove-channel-from-blacklist <value>`: Removes a channel ID from the channel blacklist
`/add-trigger-word <value>`: Adds a new trigger word to the dictionary.
`/remove-trigger-word <value>`: Removes a trigger word from the dictionary if present.
`/help`: Lists all available commands with their descriptions, along with some tips.""", ephemeral=True)


async def run_message_redaction(message: discord.Message):
    """Redacts messages if they meet the criteria"""
    has_bypass_character = message.content.startswith(settings['bypass_prefix'])
    has_image = len(message.attachments) > 0 and any('image' in attachment.content_type for attachment in message.attachments)
    is_channel_in_blacklist = message.channel.id in settings['channel_blacklist']
    is_timed_out = settings['timeout_expiration'] and datetime.now().timestamp() < settings['timeout_expiration']
    if has_bypass_character or has_image or is_channel_in_blacklist or is_timed_out:
        return
    trigger_word_indices = [i for i, word in enumerate(message.content.lower().split(' ')) if word in settings['trigger_words']]
    if trigger_word_indices or random.random() < settings['redaction_chance']:
        redacted_message = redact_message(message, trigger_word_indices)
        try:
            username = message.author.display_name
            await message.delete()
            await message.channel.send(f"{username}:\n{redacted_message}")
        except Exception as e:
            logging.error(f"Error redacting message: {e}")


async def run_reactions(message: discord.Message):
    """Reacts to messages if they meet the criteria"""
    if "js" in message.content.lower():
        try:
            await react_with_funny_letters(message, JSBAD)
        except Exception as e:
            logging.error(f"Error while reacting to message: {e}")


@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user} (ID: {client.user.id})')


@client.event
async def on_message(message: discord.Message):
    if message.author.bot: # All messages sent by any bot are ignored
        return
    await run_reactions(message)
    await run_message_redaction(message) # Run last, as it may delete the message


client.run(token)
