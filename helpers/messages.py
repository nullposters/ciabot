import logging
import os
import random
import string
import sys
from datetime import datetime
from unicodedata import lookup

import discord

sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))
from settings import settings

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

def is_bot_action_allowed_in_channel(message: discord.Message) -> bool:
    is_channel_in_blacklist = message.channel.id in settings['channel_blacklist']
    is_timed_out = settings['timeout_expiration'] and datetime.now().timestamp() < settings['timeout_expiration']
    if is_channel_in_blacklist or is_timed_out:
        return False

    return True

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
    if "http" not in message.content.lower():
        if "js" in message.content.lower():
            try:
                await react_with_funny_letters(message, JSBAD)
            except Exception as e:
                logging.error(f"Error while reacting to message: {e}")
        if message.author.id == 284876500480557056 and random.randint(1, 50) == 1: # pent's ID because funnee
            try:
                await react_with_funny_letters(message, "lib")
            except Exception as e:
                logging.error(f"Error while reacting to message: {e}")
