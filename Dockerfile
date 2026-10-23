# Use Playwright image
FROM mcr.microsoft.com/playwright/python:v1.64.1-noble@sha256:330d401ae23c905896a0c26c66c36fc971b621519e7b11b435a8328d7bf6e031

# Set environment variables
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

# Set the working directory
WORKDIR /app

# Install required system packages
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends xvfb libwebp7 \
    || (apt-get update && apt-get install -y --no-install-recommends xvfb libwebp6); \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*



# Create a non-root user with the next available UID
RUN useradd -m appuser && \
    mkdir -p /tmp/screenshots /app/data /app/logs && \
    chown -R appuser:appuser /app /tmp/screenshots /app/data /app/logs

# Update pip and install requirements as non-root user
COPY --chown=appuser:appuser requirements.txt constraints-node-security.txt ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -c constraints-node-security.txt -r requirements.txt

# Install Playwright browser
RUN playwright install --with-deps chromium

# Copy application code
COPY --chown=appuser:appuser src/ /app
COPY --chown=appuser:appuser entry.sh .

# Prepare the entry script
RUN chmod +x entry.sh

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE ${PORT}

# Run the entry script
CMD ["./entry.sh"]
