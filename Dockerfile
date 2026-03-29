FROM python:3-alpine

# Environment variables
# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# disable pip cache to reduce image size
ENV PIP_NO_CACHE_DIR=1
# use keyvault in production
ENV PYTHON_DOTENV_DISABLED=1

# Create a user and set up the working directory
RUN adduser -D flaskuser
WORKDIR /home/flaskuser

# Install dependencies
COPY . .
RUN pip install -r requirements.txt && \
    pip install gunicorn

# Set the correct permissions
RUN chmod +x start.sh && \
    chown -R flaskuser:flaskuser ./


# Switch to the non-root user
USER flaskuser

# Expose the port
EXPOSE 8080

# Run the application
CMD ["sh", "start.sh"]