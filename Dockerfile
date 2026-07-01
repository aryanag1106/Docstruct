FROM python:3.11-slim

# Install Tesseract OCR (the one system dependency DocStruct needs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml requirements.txt ./
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY sample_data/ ./sample_data/
COPY .streamlit/ ./.streamlit/

# Install Python dependencies (no GPU/CUDA wheels — CPU only)
RUN pip install --no-cache-dir -e ".[web]"

# Expose the Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit web app
CMD ["streamlit", "run", "src/docstruct/app_streamlit.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
