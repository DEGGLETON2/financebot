# Dockerfile for FinanceBot
FROM python:3.11-slim

# Prevent .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create app directory
WORKDIR /app
COPY . /app

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose Streamlit default port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "crew_tools.py", "--server.port=8501", "--server.enableCORS=false"]
