# # Stage 1: Base build stage
# FROM python:3.13-slim AS builder
 
# # Create the app directory
# RUN mkdir /app
 
# # Set the working directory
# WORKDIR /app
 
# # Set environment variables to optimize Python
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1 
 
# # Install dependencies first for caching benefit
# RUN pip install --upgrade pip 
# COPY requirements/dev.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt
 
# # Stage 2: Production stage
# FROM python:3.13-slim
 
# RUN useradd -m -r appuser && \
#    mkdir /app && \
#    chown -R appuser /app
 
# # Copy the Python dependencies from the builder stage
# COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
# COPY --from=builder /usr/local/bin/ /usr/local/bin/
 
# # Set the working directory
# WORKDIR /app
 
# # Copy application code
# COPY --chown=appuser:appuser . .
 
# # Set environment variables to optimize Python
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1 
 
# # Switch to non-root user
# USER appuser
 
# # Expose the application port
# EXPOSE 8000 

# # Make entry file executable
# RUN chmod +x  /app/entrypoint.prod.sh
 
# # Start the application using Gunicorn
# CMD ["/app/entrypoint.prod.sh"]

FROM python:3.13-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install only necessary build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/dev.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim AS runner
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -r appuser \
    && mkdir -p /app/staticfiles \
    && chown -R appuser /app

# Copy only the installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Set permissions and switch to non-root user
RUN chmod +x /app/entrypoint.prod.sh
USER appuser

# Collect static files during build
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["/app/entrypoint.prod.sh"]