import os
import logging
import discord
import jsonpickle
from settings import settings, save_settings, load_settings, change_config_value, add_elements_to_set, remove_elements_from_set
from datetime import datetime
from dotenv import load_dotenv
from collections.abc import Callable
from discord import app_commands
from bot import client


load_dotenv()
admin_id = os.getenv('ADMIN_ID')
logger = logging.getLogger(__name__)


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
    name="change-debug-channel-id",
    description="Changes debug channel ID"
)
@app_commands.describe(channel_id='The channel ID to whitelist the non prod bot to')
async def change_debug_channel_id(interaction: discord.Interaction, channel_id: str):
    message = run_if_author_is_admin(interaction, lambda: change_config_value(interaction, 'debug_channel_id', channel_id), 'debug_channel_id')
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
