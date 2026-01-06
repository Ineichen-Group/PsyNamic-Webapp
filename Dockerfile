# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y postgresql-client


# Copy the rest of the code into app directory
COPY . .

# Expose the port your app runs on (change if needed)
EXPOSE 8050

# Command to run the app
ENTRYPOINT ["./entrypoint.sh"]
