# CIABot

This is a dockerized Python project that uses the Discord.py library to run the glowiest bot in all of Discord. It'll randomly redact your messages ~~and prop up based puppet dictators in South American countries~~.

## Initial configuration

1. Install Docker.

2. Have a Papertrail log destination to log the function output to. If you don't have one, you'll need to log into (or create an account on) Papertrail, [create a new log destination](https://papertrailapp.com/destinations/new). Save the destination URL and port number.

3. A Discord Bot Account with an associated static token and the Message Content Intent enabled. If you don't have a Discord bot account, follow [this guide](https://discordpy.readthedocs.io/en/latest/discord.html). If you don't know how to enable intents, follow [this guide](https://discordpy.readthedocs.io/en/latest/intents.html). Since the bot will be reading messages, deleting them, and replacing them with its own, you should probably give it admin permissions. Save the account's secret token.

## Installation and startup

- Clone this repo

- Rename the `.env.template` file to `.env` and fill in the blanks

  - `CIABOT_TOKEN` must be your Discord Bot Account static secret token

  - `CIABOT_SETTINGS_PATH` must be the path where you want to save the bot's settings.

  - `CIABOT_ADMIN_ID` must be your Discord ID, or whoever will be the bot's admin.

  - `CIABOT_GUILD_ID` may be the Discord ID of your server, so that the slash commands won't have to wait an hour to appear. Optional.

  - `PAPERTRAIL_LOG_DESTINATION` must be your Papertrail log destination URL.

  - `PAPERTRAIL_LOG_PORT` must be your Papertrail log destination port.

- Build the docker image and run it. If you don't have any particular requirements, you can just run `source run.sh`. It will build the Docker image, tag it, prune any dangling images, run the container in detached mode with networking enabled and removal on stop, and print the container logs to your terminal in real time.

- Done! You can now glow as bright as the midday sun.

## License

This code is open sourced under the [MIT license](LICENSE)
