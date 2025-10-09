# Stage 1: Base build stage
FROM python:3.13-slim AS builder

RUN mkdir /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip
COPY requirements/dev.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production image
FROM python:3.13-slim

# Create user and necessary dirs
RUN useradd -m -r appuser && mkdir -p /app/staticfiles /app && chown -R appuser:appuser /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

WORKDIR /app

# Copy project code as appuser
COPY --chown=appuser:appuser . .

RUN chmod +x /app/entrypoint.prod.sh

USER appuser

EXPOSE 8001

CMD ["/app/entrypoint.prod.sh"]
