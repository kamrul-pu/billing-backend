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

# Stage 2: Production stage
FROM python:3.13-slim

RUN useradd -m -r appuser && \
    mkdir -p /app/staticfiles && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy app code as appuser
COPY --chown=appuser:appuser . .

# ✅ Important: Ensure permissions on mounted static dir
RUN chown -R appuser:appuser /app/staticfiles

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

USER appuser

EXPOSE 8000

RUN chmod +x /app/entrypoint.prod.sh

CMD ["/app/entrypoint.prod.sh"]
