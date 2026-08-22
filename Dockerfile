# Use official lightweight Python image
FROM python:3.10-slim

# 1. Install Linux system libraries for Tesseract OCR & OpenCV
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt-get/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# 4. Copy the rest of the application code
COPY . .

# 5. Initialize the SQLite Database inside the container
RUN python init_db.py

# 6. Expose the port
EXPOSE 5000

# 7. Start the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.app:app"]