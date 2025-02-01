# Use Python 3.12.6 slim base image
FROM python:3.11.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add a new user to avoid running as root
RUN useradd -m -u 1000 user

# Switch to the new user
USER user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:/usr/local/cuda/bin:$PATH

# Set the working directory for the application
WORKDIR $HOME/app

# Ensures both files are copied
COPY --chown=user requirements.txt .

# Install base dependencies first
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the source code  to leverage Docker cache
COPY --chown=user . .

# Expose ports for FastAPI
EXPOSE 8000

# Run both FastAPI and Streamlit
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000"]