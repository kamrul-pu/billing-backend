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

# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY requirements/dev.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create staticfiles dir and collect static at build time
RUN mkdir -p /app/staticfiles
RUN python manage.py collectstatic --noinput

# Stage 2: Production
FROM python:3.13-slim

# Create non-root user
RUN useradd -m -r appuser

WORKDIR /app

# Copy dependencies
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy entire app (including pre-collected staticfiles)
COPY --from=builder --chown=appuser:appuser /app /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

# Simplified entrypoint (no collectstatic!)
COPY --chown=appuser:appuser entrypoint.prod.sh /app/entrypoint.prod.sh
RUN chmod +x /app/entrypoint.prod.sh

CMD ["/app/entrypoint.prod.sh"]