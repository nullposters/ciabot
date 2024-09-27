docker build --no-cache -t cia_bot_public:latest . && \
docker image prune -f && \
docker run --detach --name cia-bot --network="host" --rm cia_bot_public:latest && \
docker logs cia-bot -f
