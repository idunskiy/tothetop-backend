FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
# Install system dependencies and playwright requirements
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers - Add these lines
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium
RUN playwright install-deps
RUN mkdir -p /ms-playwright && chmod 777 /ms-playwright


# Copy the rest of the application
COPY . .

# Make scripts executable
RUN chmod +x migrate.sh makemigration.sh start.sh

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]