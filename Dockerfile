# Use an official Node.js runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/ciabot/

# Copy the package.json and package-lock.json files
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# If you have environment variables, you can use .env files or pass them during runtime
# EXAMPLE: ENV NODE_ENV=production

# Command to run your bot
CMD [ "python", "bot.py" ]
