FROM python:3.10-bullseye

# Install system dependencies (ffmpeg and libopus)
RUN apt-get update && \
    apt-get install -y ffmpeg libopus0 libopus-dev git && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Run the bot
CMD ["python", "bot.py"]
