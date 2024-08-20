# Use an official Node.js runtime as a parent image
FROM node:20

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the package.json and package-lock.json files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# If you have environment variables, you can use .env files or pass them during runtime
# EXAMPLE: ENV NODE_ENV=production

# Expose the port your bot uses (if any specific port is required)
EXPOSE 3000

# Command to run your bot
CMD [ "node", "index.js" ]
