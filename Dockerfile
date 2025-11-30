# Use an official Python runtime as a parent image
FROM python:3.10.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY ./app /app/app
COPY start.sh /app/start.sh

# Make the start script executable
RUN chmod +x /app/start.sh

# Expose port 8080 for the application (Cloud Run default)
EXPOSE 8080

# Run the application using the startup script
CMD ["/app/start.sh"]