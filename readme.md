# CIABot

This is a dockerized TypeScript project that uses the discord.js and discordx libraries to run the glowiest bot in all of Discord. It'll randomly redact your messages, react to messages, ~~and prop up based puppet dictators in South American countries~~.

## Initial configuration

1. Install Docker.

2. We recommend you set up a log destination. Bot has a config available for Datadog, other providers coming soon™. If you don't add one, localhost:514 will be used.

3. A Discord Bot Account with an associated static token and the Message Content Intent enabled. If you don't have a Discord bot account, follow [this guide](https://discordjs.guide/preparations/setting-up-a-bot-application.html). If you don't know how to enable intents, follow [this guide](https://discordjs.guide/popular-topics/intents.html#privileged-intents). Since the bot will be reading messages, reacting to them, or deleting them, and replacing them with its own, you should probably give it admin permissions. Save the account's secret token, for security reasons this token will only be shown once; to see it again you must regenerate the token.

## Installation and startup

- Clone this repo

- Rename the `.env.template` file to `.env` and fill in the blanks

  - `CIABOT_TOKEN` must be your Discord Bot Account static secret token.

  - `CIABOT_APPID` must be your Discord Bot's App ID.

  - `CIABOT_SETTINGS_PATH` must be the path where you want to save the bot's settings.

  - `CIABOT_ADMIN_ID` must be your Discord ID, or whoever will be the bot's admin.

  - `CIABOT_GUILD_ID` may be the Discord ID of your server, so that the slash commands won't have to wait an hour to appear. Optional.

  - `LOG_DESTINATION` may be `datadog` or your log destination URL. Optional.

  - `LOG_PORT` may be your log destination port. Optional.

  - `POSTGRES_DB` for the PostgreSQL database name you plan to use. This will be packaged up by Docker in docker-compose.
  
  - `POSTGRES_USER` for the PostgreSQL database username you plan to use.
  
  - `POSTGRES_PASSWORD` for the PostgreSQL database password you plan to use.
  
  - `POSTGRES_HOST` for the PostgreSQL host, default to `db`
  
  - `IS_PRODUCTION` the value for if the running instance of the bot is a production environment

  - `DEBUG_CHANNEL_ID` the ID of the Discord channel a non-production instance of the bot will exclusively work in

  - `DD_APIKEY` must be your datadog api key

  - `DD_HOSTNAME` required value, recommended that you set this to the bot's image name

  - `DD_SERVICE` required value, set it to something like `discord-ciabot`

  - `DD_TAGS` must be at least on kv pair, recommened that it's set to the environment the bot is being deployed in (e.g. `environment:sandbox`)

- Build the docker image and run it. If you don't have any particular requirements, you can just run `source run.sh`. It will build the Docker image, tag it, prune any dangling images, run the container in detached mode with networking enabled and removal on stop, and print the container logs to your terminal in real time.

- Done! You can now glow as bright as the midday sun.

## ɴᴜʟʟposting
If you've somehow managed to stumble across this bot outside our little developer community, join us on [Programmer ɴᴜʟʟposting](https://www.facebook.com/groups/programmer.nullposting), or on our [Discord server](https://discord.gg/nullclub)

## License

This code is open sourced under the [MIT license](LICENSE)
