import os
import logging
import discord
import jsonpickle
from typing import Any
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)
settings_path = os.getenv('CIABOT_SETTINGS_PATH', 'settings.json')


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
