# WorkHub - Docker Deployment Guide

This guide explains how to deploy the WorkHub Task Management System using Docker.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose installed (included with Docker Desktop)
- At least 4GB of RAM available
- Ports 3000 (frontend), 5000 (backend), and 1433 (database) available

## Quick Start

### 1. Configure Environment Variables

Copy the `.env.example` file to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` and set your values:

```env
# Required: Database password (must be strong)
SA_PASSWORD=YourStrong!Passw0rd123

# Optional: Email notifications (leave blank to disable)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
EMAIL_NOTIFICATIONS_ENABLED=False
```

**Note**: The database password must meet SQL Server requirements:
- At least 8 characters
- Contains uppercase, lowercase, numbers, and special characters

### 2. Build and Start Services

Build the Docker images:

```bash
docker-compose build
```

Start all services:

```bash
docker-compose up -d
```

### 3. Access the Application

- **Frontend (React)**: http://localhost:3000
- **Backend API**: http://localhost:5000/api
- **Database**: localhost:1433 (SQL Server)

### 4. Default Login

The system automatically creates an admin user:

- **Username**: admin
- **Password**: admin123

**Important**: Change the admin password immediately after first login!

## Docker Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove All Data

```bash
docker-compose down -v
```

### Restart Services

```bash
docker-compose restart
```

### Rebuild After Code Changes

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Nginx     │────▶│    Flask     │────▶│  SQL Server  │
│  (Frontend) │     │   (Backend)  │     │  (Database)  │
│   :3000     │     │     :5000    │     │    :1433     │
└─────────────┘     └──────────────┘     └──────────────┘
```

## Troubleshooting

### Database Connection Issues

If the backend can't connect to the database:

1. Check database health:
   ```bash
   docker-compose ps
   ```

2. Wait for database initialization (can take 1-2 minutes on first run)

3. Check database logs:
   ```bash
   docker-compose logs database
   ```

### Frontend Can't Reach Backend

Check nginx configuration:

```bash
docker-compose logs frontend
```

Verify backend is running:

```bash
curl http://localhost:5000/api/health
```

### Port Already in Use

If ports are already in use, edit `docker-compose.yml`:

```yaml
ports:
  - "8080:80"  # Change 3000 to 8080 for frontend
  - "8000:5000"  # Change 5000 to 8000 for backend
```

### Rebuilding Specific Service

```bash
docker-compose build backend
docker-compose up -d backend
```

## Production Deployment

### Security Checklist

- [ ] Change default admin password
- [ ] Update `SECRET_KEY` and `JWT_SECRET_KEY` in docker-compose.yml
- [ ] Use strong database password
- [ ] Configure HTTPS/SSL (use nginx-proxy or similar)
- [ ] Enable email notifications
- [ ] Set up regular backups
- [ ] Configure firewall rules
- [ ] Review and update CORS settings

### Performance Optimization

1. **Resource Limits**: Add resource constraints in docker-compose.yml

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

2. **Database Tuning**: Mount custom SQL Server configuration

3. **Scaling**: Use Docker Swarm or Kubernetes for multi-instance deployment

## Data Persistence

All data is stored in Docker volumes:

- `mssql_data`: Database files
- `./workhub-backend/uploads`: User-uploaded files

### Backup

```bash
# Backup database volume
docker run --rm -v mssql_data:/data -v $(pwd):/backup ubuntu tar czf /backup/db-backup-$(date +%Y%m%d).tar.gz /data

# Backup uploads
tar czf uploads-backup-$(date +%Y%m%d).tar.gz workhub-backend/uploads
```

### Restore

```bash
# Restore database volume
docker run --rm -v mssql_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/db-backup-YYYYMMDD.tar.gz -C /

# Restore uploads
tar xzf uploads-backup-YYYYMMDD.tar.gz
```

## Monitoring

View container resource usage:

```bash
docker stats
```

Check health status:

```bash
docker-compose ps
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Verify environment variables are correct
3. Ensure all ports are available
4. Check Docker Desktop is running

## License

[Your License Here]

