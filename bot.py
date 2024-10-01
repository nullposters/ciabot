import os
import logging
import discord
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)
token = os.getenv('CIABOT_TOKEN', os.getenv('CIABOT_SECRET')) # Backwards compatible with the original token name
test_guild = discord.Object(os.getenv('CIABOT_GUILD_ID')) if os.getenv('CIABOT_GUILD_ID') else None


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
        self.tree = discord.app_commands.CommandTree(self)

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


client.run(token)
