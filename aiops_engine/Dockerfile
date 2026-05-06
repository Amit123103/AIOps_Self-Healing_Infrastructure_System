# === FILE: aiops_engine/Dockerfile ===
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for some ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the pipeline and the FastAPI backend together
# In a real scenario, these might be separate containers
# For demonstration, we'll start both using a shell script
RUN echo '#!/bin/bash\n\
python pipeline.py &\n\
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}\n\
' > start.sh && chmod +x start.sh

EXPOSE 8001
CMD ["./start.sh"]
