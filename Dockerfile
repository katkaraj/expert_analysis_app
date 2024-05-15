# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install openpyxl

# Expose the port number on which the Dash app will run
EXPOSE 8050

# Command to run the Dash app using Gunicorn
CMD exec gunicorn --bind :8050 app:server