# Coolify Deployment Guide for Billing Backend

This guide will help you deploy your Django billing backend to a VPS using Coolify with Nginx for static file serving.

## Prerequisites

- VPS with Coolify installed
- Domain name pointing to your VPS
- PostgreSQL database (can be hosted on the same VPS or external)
- Basic understanding of Docker and environment variables

## Project Structure

The project has been optimized for production deployment with:

- **Multi-stage Dockerfile** for optimized image size
- **Nginx configuration** for static file serving and reverse proxy
- **Health checks** for container monitoring
- **Production-ready settings** with security headers
- **Static file collection** during build process

## Deployment Steps

### 1. Prepare Your Repository

1. Push your code to a Git repository (GitHub, GitLab, etc.)
2. Ensure all files are committed and pushed

### 2. Set Up Database

#### Option A: External PostgreSQL Database
- Create a PostgreSQL database on your VPS or use a managed service
- Note down the connection details

#### Option B: Add PostgreSQL to Coolify
- In Coolify, create a new PostgreSQL service
- Note the connection string

### 3. Configure Environment Variables

1. Copy `env.production.example` to `.env` in your project root
2. Update the following variables:

```bash
# Required Variables
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://username:password@host:port/database_name
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Mikrotik Configuration (if applicable)
MIKROTIK_URL=http://your-mikrotik-ip
MIKROTIK_USER=your-username
MIKROTIK_PASS=your-password

# Optional
ENABLE_DOC=True
ENABLE_SILK=False
```

### 4. Deploy with Coolify

1. **Create New Application**
   - Go to your Coolify dashboard
   - Click "New Application"
   - Choose "Docker Compose" as the source

2. **Configure Repository**
   - Connect your Git repository
   - Set the branch (usually `main` or `development`)
   - Set the build context to the project root

3. **Set Environment Variables**
   - Add all environment variables from your `.env` file
   - Make sure to set `DEBUG=False` for production

4. **Configure Ports**
   - The application will run on port 80 (Nginx)
   - Internal Django app runs on port 8000

5. **Deploy**
   - Click "Deploy" and wait for the build process
   - Monitor the logs for any issues

### 5. Post-Deployment Configuration

1. **Create Superuser**
   ```bash
   # Access the running container
   docker exec -it billing-backend-web bash
   
   # Create superuser
   python manage.py createsuperuser
   ```

2. **Verify Deployment**
   - Visit `https://your-domain.com/health/` - should return JSON with status
   - Visit `https://your-domain.com/admin/` - Django admin interface
   - Visit `https://your-domain.com/api/docs/` - API documentation (if enabled)

## Configuration Files

### Dockerfile
- Multi-stage build for optimized image size
- Collects static files during build
- Runs as non-root user for security

### Nginx Configuration (`nginx/default.conf`)
- Serves static files directly
- Reverse proxy for Django application
- Security headers and compression
- Health check endpoint

### Docker Compose
- Two services: Django app and Nginx
- Shared volumes for static and media files
- Health checks for both services
- Proper dependency management

## Monitoring and Maintenance

### Health Checks
- Application health: `https://your-domain.com/health/`
- Nginx health: Built-in health check

### Logs
- View logs in Coolify dashboard
- Django logs: Application container
- Nginx logs: Nginx container

### Static Files
- Static files are collected during build
- Served directly by Nginx for better performance
- Cached for 30 days with proper headers

### Database Migrations
- Migrations run automatically on container start
- Database is checked before starting the application

## Troubleshooting

### Common Issues

1. **Static files not loading**
   - Check if static files are collected: `python manage.py collectstatic`
   - Verify Nginx configuration
   - Check volume mounts

2. **Database connection issues**
   - Verify `DATABASE_URL` format
   - Check database accessibility
   - Ensure database exists and user has permissions

3. **CORS issues**
   - Update `CORS_ALLOWED_ORIGINS` with your frontend domain
   - Check `DJANGO_CSRF_TRUSTED_ORIGINS`

4. **Health check failures**
   - Check if Django app is running on port 8000
   - Verify health check endpoint is accessible

### Debug Mode
To enable debug mode temporarily:
1. Set `DEBUG=True` in environment variables
2. Redeploy the application
3. Check logs for detailed error messages

## Security Considerations

- Never commit `.env` files to version control
- Use strong, unique `SECRET_KEY`
- Keep `DEBUG=False` in production
- Regularly update dependencies
- Use HTTPS in production
- Configure proper CORS and CSRF settings

## Performance Optimization

- Static files are served by Nginx (faster than Django)
- Gzip compression enabled
- Proper caching headers
- Database connection pooling
- Gunicorn with multiple workers

## Backup Strategy

1. **Database Backups**
   - Set up regular PostgreSQL backups
   - Store backups in a secure location

2. **Media Files**
   - Media files are stored in Docker volumes
   - Consider backing up the `media_volume`

3. **Code Backups**
   - Code is in Git repository
   - Keep multiple remotes for redundancy

## Scaling

For high-traffic applications:
- Increase Gunicorn workers
- Use external Redis for caching
- Consider database read replicas
- Implement CDN for static files
- Use load balancer for multiple instances

## Support

If you encounter issues:
1. Check the application logs in Coolify
2. Verify all environment variables are set correctly
3. Test the health check endpoint
4. Check database connectivity
5. Review the troubleshooting section above
