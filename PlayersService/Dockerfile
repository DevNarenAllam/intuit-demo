FROM python:3.12-slim

# Set a default value for PORT if not provided
ARG PORT=8001
ENV PORT=$PORT

# Create a non-root user and group
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY PlayersService/. /app
RUN mkdir -p /app/Common
COPY Common/. /app/Common

# Change ownership of /app to appuser
RUN chown -R appuser:appgroup /app

# Ensure the start script is executable
RUN chmod +x /app/Common/start.sh

# Change to the non-root user
USER appuser

# Expose the port
EXPOSE $PORT

# Command to run the application
CMD ["/app/Common/start.sh"]