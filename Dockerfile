# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code to the working directory
COPY . .

# The default command to run when the container starts.
# We use tail -f /dev/null to keep the container running so we can exec into it
# or use `docker-compose run` for our commands.
CMD ["tail", "-f", "/dev/null"]
