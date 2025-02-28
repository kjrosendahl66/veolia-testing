FROM python:3.10-slim

# Set environment variables
WORKDIR /app

# Install system dependencies, including pandoc
RUN apt-get update && \
    apt-get install -y make gcc g++ libjpeg-dev libpng-dev libtiff-dev zlib1g-dev libmupdf-dev pandoc texlive-latex-recommended texlive-fonts-extra && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
 
# Copy the requirements file into the container
COPY requirements.txt requirements.txt
 
# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . . 

# Expose the port 
EXPOSE 8080

# Specify the command to run on container startup
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8080"]
