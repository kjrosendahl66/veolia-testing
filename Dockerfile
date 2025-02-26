FROM python:3.10.13-slim-bookworm

WORKDIR /app
COPY . /app

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Streamlit runs on (default is 8501)
EXPOSE 8080

# Specify the command to run on container startup
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8080"]
