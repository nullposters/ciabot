import os
import json
import socket
import random
import logging
import discord
from dotenv import load_dotenv
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
    

syslog = SysLogHandler(address=(os.getenv('PAPERTRAIL_LOG_DESTINATION'), int(os.getenv('PAPERTRAIL_LOG_PORT'))), facility=SysLogHandler.LOG_USER)
syslog.addFilter(ContextFilter())
format = '%(asctime)s %(hostname)s cia_bot: %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(syslog)
logger.setLevel(logging.INFO)
# End logging initialization


token = os.getenv('CIABOT_SECRET', os.getenv('CIABOT_TOKEN'))
admin_id = os.getenv('CIABOT_ADMIN_ID')
settings_path = os.getenv('CIABOT_SETTINGS_PATH', 'settings.json')
test_guild = discord.Object(os.getenv('CIABOT_GUILD_ID'))


def save_settings() -> None:
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)


def load_settings() -> dict[str, float | list[str]]:
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            if settings.get('redaction_chance') is None:
                settings['redaction_chance'] = 0.08
            if settings.get('selection_chance') is None:
                settings['selection_chance'] = 0.005
            if settings.get('trigger_words') is None:
                settings['trigger_words'] = []
            if settings.get('trigger_word_chance') is None:
                settings['trigger_word_chance'] = 0.1
            if settings.get('bypass_prefix') is None:
                settings['bypass_prefix'] = '>>'
            return settings
    else:
        return {
            'redaction_chance': 0.08,
            'selection_chance': 0.005,
            'trigger_words': [],
            'trigger_word_chance': 0.1,
            'bypass_prefix': '>>'
        }


settings = load_settings()
save_settings()


REDACTED = "`[REDACTED]`"


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
    message_id = message.id
    message_author = message.author.name
    return message_id, message_author


def redact_message(message: discord.Message, trigger_word_indices: list[int]) -> str:
    message_id, message_author = extract_message_metadata(message)
    logging.info(f"Processing message {message_id=}, {message_author=}, {'has trigger word' if trigger_word_indices else 'randomly selected'}")
    message_content = message.content.split(' ')
    was_redacted = False
    indices = trigger_word_indices if trigger_word_indices else range(len(message_content))
    threshold = settings['trigger_word_chance'] if trigger_word_indices else settings['redaction_chance']
    for idx in indices:
        if random.random() < threshold:
            message_content[idx] = REDACTED
            was_redacted = True
    if not was_redacted:
        random_index = random.choice(indices)
        message_content[random_index] = REDACTED
    return ' '.join(message_content)


def check_if_author_is_admin(interaction: discord.Interaction) -> bool:
    is_mod = any("mod" in role.name or "Mod" in role.name for role in interaction.user.roles)
    can_manage_messages = interaction.user.top_role.permissions.manage_messages
    is_admin = interaction.user.top_role.permissions.administrator
    is_bot_owner = interaction.user.id == int(admin_id)
    return is_mod or can_manage_messages or is_admin or is_bot_owner


def run_if_author_is_admin(interaction: discord.Interaction, function: Callable[[str, float], None], param_name: str, element: str = None) -> str:
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


@client.tree.command(
    name="change-bypass-prefix",
    description="Changes the prefix that allows bypassing the bot"
)
@app_commands.describe(new_prefix='The new prefix to bypass the bot')
async def change_bypass_prefix(interaction: discord.Interaction, new_prefix: str):
    def logic():
        logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Changing bypass prefix to {new_prefix}")
        settings['bypass_prefix'] = new_prefix
        save_settings()
    message = run_if_author_is_admin(interaction, logic, 'bypass_prefix')
    await interaction.response.send_message(message, ephemeral=True)


def change_config_value(config_key: str, new_value: float) -> None:
    logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Changing config value {config_key} to {new_value}")
    settings[config_key] = new_value/100.0
    save_settings()


@client.tree.command(
    name="change-selected-chance",
    description="Changes the chance to select any random message for redaction"
)
@app_commands.describe(new_chance='The new threshold of the selection check that will be applied to all messages for possible redaction. Goes from 0% to 100%.')
async def change_chance(interaction: discord.Interaction, new_chance: app_commands.Range[float, 0, 100]):
    message = run_if_author_is_admin(interaction, lambda: change_config_value('selection_chance', new_chance), 'selection_chance')
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="change-redacted-chance",
    description="Changes the chance to redact any random word in a selected message"
)
@app_commands.describe(new_chance='The new threshold of the redaction check that will be applied to all the words in a selected message. Goes from 0% to 100%. If all words pass the check, one random word will be redacted.')
async def change_redacted(interaction: discord.Interaction, new_chance: app_commands.Range[float, 0, 100]):
    message = run_if_author_is_admin(interaction, lambda: change_config_value('redaction_chance', new_chance), 'redaction_chance')
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="change-trigger-word-chance",
    description="Changes the chance to redact a trigger word"
)
@app_commands.describe(new_chance='The new threshold of the redaction check that will be applied to all the trigger words of any message. Goes from 0% to 100%. If all words pass the check, one random trigger word will be redacted.')
async def change_trigger_word_chance(interaction: discord.Interaction, new_chance: app_commands.Range[float, 0, 100]):
    message = run_if_author_is_admin(interaction, lambda: change_config_value('trigger_word_chance', new_chance), 'trigger_word_chance')
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="show-values",
    description="Shows the current configuration values"
)
async def show_values(interaction: discord.Interaction):
    logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Showing configuration values")
    redaction_chance = settings['redaction_chance']
    chance = settings['selection_chance']
    trigger_word_chance = settings['trigger_word_chance']
    trigger_words = settings['trigger_words']
    bypass_prefix = settings['bypass_prefix']
    await interaction.response.send_message(f"Selection chance: {chance:.2%}\nRedaction chance: {redaction_chance:.2%}\nTrigger word chance: {trigger_word_chance:.2%}\nBypass prefix: `{bypass_prefix}`\nTrigger words: {', '.join(trigger_words)}", ephemeral=True)


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
    name="add-trigger-word",
    description="Adds a trigger word to the list of words that trigger the bot"
)
@app_commands.describe(new_trigger_word='The new trigger word to add to the list')
async def add_trigger_word(interaction: discord.Interaction, new_trigger_word: str):
    def logic():
        logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Adding trigger word {new_trigger_word}")
        settings['trigger_words'].append(new_trigger_word.lower())
        save_settings()
    message = run_if_author_is_admin(interaction, logic, 'trigger_words', new_trigger_word)
    await interaction.response.send_message(message, ephemeral=True)


@client.tree.command(
    name="remove-trigger-word",
    description="Removes a trigger word from the list of words that trigger the bot"
)
@app_commands.describe(old_trigger_word='The trigger word to remove from the list')
async def remove_trigger_word(interaction: discord.Interaction, old_trigger_word: str):
    def logic():
        logger.info(f"Received command from {interaction.user.name} (ID: {interaction.user.id}): Removing trigger word {old_trigger_word}")
        settings['trigger_words'].remove(old_trigger_word.lower())
        save_settings()
    message = run_if_author_is_admin(interaction, logic, 'trigger_words', old_trigger_word)
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
`/add-trigger-word <value>`: Adds a new trigger word to the dictionary.
`/remove-trigger-word <value>`: Removes a trigger word from the dictionary if present.
`/help`: Lists all available commands with their descriptions, along with some tips.""", ephemeral=True)


@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user} (ID: {client.user.id})')


@client.event
async def on_message(message: discord.Message):
    is_self = message.author.id == client.user.id
    has_bypass_character = message.content.startswith(settings['bypass_prefix'])
    has_image = len(message.attachments) > 0 and any('image' in attachment.content_type for attachment in message.attachments)
    if is_self or has_bypass_character or has_image:
        return
    trigger_word_indices = [i for i, word in enumerate(message.content.lower().split(' ')) if word in settings['trigger_words']]
    if trigger_word_indices or random.random() < settings['redaction_chance']:
        redacted_message = redact_message(message, trigger_word_indices)
        try:
            username = message.author.name
            await message.delete()
            await message.channel.send(f"{username}:\n{redacted_message}")
        except Exception as e:
            logging.error(f"Error redacting message: {e}")
                    

client.run(token)
