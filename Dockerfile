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

# ---------- Stage 1: Build (installs deps) ----------
FROM python:3.13-slim AS builder

WORKDIR /app

# Avoid writing .pyc and keep stdout clean
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/dev.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files (so they exist before deploy)
RUN mkdir -p /staticfiles && \
    python manage.py collectstatic --noinput


# ---------- Stage 2: Runtime ----------
FROM python:3.13-slim

# Create app user
RUN useradd -m -r appuser && \
    mkdir -p /app /staticfiles && \
    chown -R appuser:appuser /app /staticfiles

# Copy Python deps and built static files
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy app code
COPY --from=builder /app /app
COPY --from=builder /staticfiles /staticfiles

WORKDIR /app

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set ownership
RUN chown -R appuser:appuser /app /staticfiles

# Expose port
EXPOSE 8000

# Run as non-root
USER appuser

# Make entrypoint executable
RUN chmod +x /app/entrypoint.prod.sh

CMD ["/app/entrypoint.prod.sh"]