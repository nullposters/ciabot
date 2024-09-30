# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/ciabot/

# Copy the requirements.txt file
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install psycopg2 for PostgreSQL
RUN apt-get update && apt-get install -y libpq-dev gcc && pip install psycopg2

# Copy the rest of the application code
COPY . .

# Command to run your bot
CMD [ "python", "bot.py" ]