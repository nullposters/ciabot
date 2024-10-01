import os
import random
import string
import discord
import logging
from bot import client
from datetime import datetime
from settings import settings
from unicodedata import lookup


token = os.getenv('CIABOT_SECRET', os.getenv('CIABOT_TOKEN')) # Backwards compatible with the original token name
test_guild = discord.Object(os.getenv('CIABOT_GUILD_ID'))


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


def redact_message(message: discord.Message, trigger_word_indices: list[int]) -> str:
    """Redacts a given message. If the message contains trigger words, redacts any word at random from the trigger words. Otherwise, redacts any random word from the message."""
    message_id, message_author = message.id, message.author.name
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


async def react_with_funny_letters(message: discord.Message, text: str):
    """Reacts to a message with single-letter emojis. The string to emulate is deduplicated before reacting."""
    upper_text = text.upper()
    letter_set = set(upper_text)
    if any(c not in set(string.ascii_uppercase) for c in letter_set):
        return
    for char in upper_text:
        await message.add_reaction(lookup(f'REGIONAL INDICATOR SYMBOL LETTER {char}'))


async def run_message_redaction(message: discord.Message):
    """Redacts messages if they meet the criteria"""
    has_bypass_character = message.content.startswith(settings['bypass_prefix'])
    has_image = len(message.attachments) > 0 and any('image' in attachment.content_type for attachment in message.attachments)
    is_whitelist_enabled = bool(settings['channel_whitelist'])
    is_channel_in_whitelist = message.channel.id in settings['channel_whitelist']
    is_channel_in_blacklist = message.channel.id in settings['channel_blacklist']
    is_timed_out = settings['timeout_expiration'] and datetime.now().timestamp() < settings['timeout_expiration']
    if has_bypass_character or has_image or is_channel_in_blacklist or is_timed_out or (is_whitelist_enabled and not is_channel_in_whitelist):
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
