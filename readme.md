# CIABot

## Initial configuration
1. Create discord app in discord developer site with admin permissions (he needs to be able to delete and create messages, this is required)
2. Note his ID and secret


## Installation and startup
1. Run `npm install`
2. In your `.env` file:
   1. Set `ciaBotId` (string) to the ID you noted in the creation of the discord app.
   2. Set `secret` (string) to the secret you noted in the creation of the discord app.
   3. Set `adminId` (string) to your discord ID, or whoever will be the administrator of the bot. 
3. Run `node index.js`
4. Done

## Deployment to Linux
Do this:
1. `cd C:\Path\To\Your\Bot`
2. `docker build -t cia-bot-public .`
3. `docker tag my-discord-bot your_dockerhub_username/cia-bot-public`
4. `docker push your_dockerhub_username/cia-bot-public`
5. SSH into where it will be hosted
6. `mkdir -p /root/ciabot-public/data`
7. `docker pull your_dockerhub_username/cia-bot-public`
8. `docker run -d -v /root/ciabot-public/data:/usr/src/app --name cia-bot-container -p 80:3000 your_dockerhub_username/my-discord-bot`