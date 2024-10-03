# Use an official Python runtime as a builder image
FROM python:3.11-slim AS builder

# Install libpq and gcc to compile psycopg2
RUN apt update && \
    apt install -y libpq-dev gcc && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install virtualenv && \
    virtualenv /usr/ciabot/.venv/

# Activate the virtual environment
ENV PATH="/usr/ciabot/.venv/bin:$PATH"

# Copy the requirements.txt file
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install libpq to run psycopg2
RUN apt update && \
    apt install -y libpq5 && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the previous image
COPY --from=builder /usr/ciabot/.venv /usr/ciabot/.venv

# Set the working directory in the container
WORKDIR /usr/ciabot/

# Don't write .pyc files, don't buffer output, and activate the virtual environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/ciabot/.venv/bin:$PATH"

# Copy just the code files
COPY . ./

# Command to run your bot
CMD [ "python", "bot.py" ]
