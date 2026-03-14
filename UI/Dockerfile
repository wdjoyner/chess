FROM python:3.14

# Install Stockfish inside the container so it's fully self-contained
RUN apt-get update && apt-get install -y \
    stockfish \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set an environment variable for the internal Stockfish path
ENV STOCKFISH_PATH=/usr/games/stockfish

# Expose the default Streamlit port
EXPOSE 8501

# Healthcheck to ensure the container is serving the UI properly
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit bound to 0.0.0.0 to ensure localhost access works
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]