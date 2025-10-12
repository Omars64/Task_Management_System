# Work Hub - Production Deployment Guide

This guide covers deploying the Work Hub Task Management System to production.

## Prerequisites

- Docker and Docker Compose installed
- Domain name configured
- SSL certificates (Let's Encrypt recommended)
- Server with at least 2GB RAM and 20GB storage

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd workhub
   ```

2. **Configure environment variables**
   ```bash
   cp .env.prod.example .env.prod
   # Edit .env.prod with your production values
   ```

3. **Deploy**
   ```bash
   ./deploy.sh
   ```

## Manual Deployment

### 1. Environment Configuration

Create `.env.prod` file with the following variables:

```bash
# Database Configuration
MYSQL_ROOT_PASSWORD=your_secure_root_password_here
MYSQL_DATABASE=workhub
MYSQL_USER=workhub_user
MYSQL_PASSWORD=your_secure_database_password_here

# Application Secrets (CHANGE THESE!)
SECRET_KEY=your_super_secret_key_here_change_this_in_production
JWT_SECRET_KEY=your_jwt_secret_key_here_change_this_in_production

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_DEFAULT_SENDER=your_email@gmail.com

# Application URLs
FRONTEND_URL=https://your-domain.com
```

### 2. SSL Certificates

Place your SSL certificates in the `nginx/ssl/` directory:
- `nginx/ssl/cert.pem` - SSL certificate
- `nginx/ssl/key.pem` - Private key

For Let's Encrypt:
```bash
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

### 3. Deploy Services

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up --build -d

# Check service health
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Initialize Database

```bash
# Initialize database with sample data
docker-compose -f docker-compose.prod.yml exec backend python init_db.py
```

## Security Considerations

### 1. Environment Variables
- Use strong, unique passwords
- Generate secure random keys for SECRET_KEY and JWT_SECRET_KEY
- Never commit `.env.prod` to version control

### 2. Database Security
- Use strong database passwords
- Consider using MySQL's authentication plugins
- Enable SSL for database connections

### 3. Network Security
- Configure firewall rules
- Use HTTPS only
- Implement rate limiting
- Regular security updates

### 4. Application Security
- Change default admin credentials
- Implement proper backup strategy
- Monitor logs for suspicious activity
- Regular security audits

## Monitoring and Maintenance

### Health Checks
- Frontend: `https://your-domain.com/health`
- Backend: `https://your-domain.com/api/health`

### Logs
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Backups
```bash
# Database backup
docker-compose -f docker-compose.prod.yml exec mysql mysqldump -u root -p workhub > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T mysql mysql -u root -p workhub < backup_file.sql
```

### Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose -f docker-compose.prod.yml up --build -d

# Run database migrations (if any)
docker-compose -f docker-compose.prod.yml exec backend python init_db.py
```

## Scaling

### Horizontal Scaling
- Use load balancer for multiple backend instances
- Implement database clustering
- Use Redis for session storage

### Vertical Scaling
- Increase container resources
- Optimize database queries
- Implement caching strategies

## Troubleshooting

### Common Issues

1. **Services not starting**
   - Check logs: `docker-compose -f docker-compose.prod.yml logs`
   - Verify environment variables
   - Check port conflicts

2. **Database connection issues**
   - Verify MySQL is running
   - Check database credentials
   - Ensure network connectivity

3. **SSL certificate issues**
   - Verify certificate files exist
   - Check certificate validity
   - Ensure proper file permissions

4. **Email not working**
   - Verify SMTP credentials
   - Check firewall rules
   - Test SMTP connection

### Performance Optimization

1. **Database**
   - Add indexes for frequently queried columns
   - Optimize queries
   - Configure connection pooling

2. **Application**
   - Enable gzip compression
   - Implement caching
   - Optimize images and assets

3. **Infrastructure**
   - Use CDN for static assets
   - Implement database read replicas
   - Use Redis for caching

## Support

For issues and questions:
- Check the logs first
- Review this documentation
- Create an issue in the repository
- Contact the development team

## License

This project is licensed under the MIT License - see the LICENSE file for details.