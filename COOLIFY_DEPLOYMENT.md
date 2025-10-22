# Coolify Deployment Guide

This guide will help you deploy the billing-backend Django application on Coolify with Redis and Celery support.

## Prerequisites

- Coolify instance running
- PostgreSQL database (can be provided by Coolify or external)
- Domain name (optional, for custom domain)

## Deployment Steps

### 1. Environment Variables

Set the following environment variables in Coolify:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ENABLE_SILK=False
ENABLE_DOC=False

# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database_name

# Django Security Settings
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Mikrotik Configuration
MIKROTIK_URL=http://your-mikrotik-ip
MIKROTIK_USER=your-mikrotik-username
MIKROTIK_PASS=your-mikrotik-password

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 2. Coolify Configuration

1. **Create a new project** in Coolify
2. **Connect your Git repository** containing this code
3. **Select Docker Compose** as the deployment method
4. **Use the provided `coolify.yml`** file for configuration

### 3. Services Overview

The deployment includes the following services:

- **web**: Django application server (Gunicorn)
- **redis**: Redis server for Celery broker and caching
- **celery-worker**: Background task processor
- **celery-beat**: Periodic task scheduler

### 4. Static Files

Static files are automatically collected and served by the Django application. The `staticfiles` volume is shared across all services.

### 5. Database Migrations

Database migrations are automatically run during the web service startup.

### 6. Health Checks

The application includes health checks for:
- Database connectivity
- Redis connectivity
- Celery worker status

## Custom Domain Setup

If you want to use a custom domain:

1. Add your domain to the `DJANGO_ALLOWED_HOSTS` environment variable
2. Add your domain to `DJANGO_CSRF_TRUSTED_ORIGINS`
3. Add your domain to `CORS_ALLOWED_ORIGINS`
4. Configure your domain in Coolify's domain settings

## Monitoring

- Check the Coolify logs for any issues
- Monitor Redis memory usage
- Check Celery worker logs for task processing
- Monitor database connections

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Verify `DATABASE_URL` is correct
   - Check if database is accessible from Coolify

2. **Redis Connection Issues**
   - Verify Redis service is running
   - Check `CELERY_BROKER_URL` configuration

3. **Static Files Not Loading**
   - Check if `collectstatic` command ran successfully
   - Verify static files volume is mounted correctly

4. **Celery Tasks Not Processing**
   - Check celery-worker service logs
   - Verify Redis connectivity
   - Check task definitions in `customer/tasks.py`

### Logs

Access logs through Coolify's interface:
- Web service logs: Django application logs
- Celery worker logs: Background task processing
- Celery beat logs: Scheduled task logs
- Redis logs: Database and cache logs

## Production Considerations

1. **Security**
   - Use strong `SECRET_KEY`
   - Set `DEBUG=False`
   - Configure proper `ALLOWED_HOSTS`
   - Use HTTPS in production

2. **Performance**
   - Adjust Gunicorn workers based on CPU cores
   - Configure Redis memory limits
   - Monitor database connection pool

3. **Backup**
   - Regular database backups
   - Redis data persistence
   - Static files backup

## Support

For issues specific to this deployment, check:
- Django logs in Coolify
- Celery worker logs
- Redis logs
- Database connection logs
