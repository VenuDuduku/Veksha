# Use Python 3.10 base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files to the container
COPY . .

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Expose port (Flask uses 5000 by default)
EXPOSE 5000

# Start the app using gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
