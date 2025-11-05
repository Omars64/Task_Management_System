# WorkHub Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker Desktop installed
- Docker Compose installed
- Your email credentials (Gmail recommended)

### Setup Steps

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Task_Management_System-1
```

2. **Configure Email (Required for verification codes)**

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your email credentials:
```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**Getting Gmail App Password:**
1. Go to Google Account settings
2. Security → 2-Step Verification (enable it)
3. Security → App passwords
4. Generate password for "Mail"
5. Copy the 16-character password (with spaces)

3. **Start the Application**

```bash
docker-compose up --build
```

This will:
- Build frontend and backend containers
- Start SQL Server database
- Run database migrations
- Start all services

4. **Access the Application**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000/api/health
- **Database**: localhost:1433

### Default Admin Credentials

First user created will be admin. Or use:
- **Email**: admin@workhub.com
- **Password**: (set during first login)

### Stopping the Application (Non-Destructive)

```bash
docker-compose down
```

⚠ Important: Do NOT run `docker-compose down -v` unless you intentionally want to DELETE your database volume. This permanently removes all users/tasks.

### Backups and Restore

- Create backup (Windows PowerShell):
```bash
powershell -File scripts/backup-db.ps1
```

- Restore from backup (Windows PowerShell):
```bash
powershell -File scripts/restore-db.ps1 -BackupPath .\\backup-YYYYMMDD-HHMMSS.bak
```

- Create backup (Bash):
```bash
SA_PASSWORD=yourpassword ./scripts/backup-db.sh
```

- Restore from backup (Bash):
```bash
SA_PASSWORD=yourpassword ./scripts/restore-db.sh workhub-db workhub ./backup-YYYYMMDD-HHMMSS.bak
```

---

## Architecture

```
┌─────────────────┐
│   Frontend      │  :3000
│   (React/Vite)  │  Nginx
└────────┬────────┘
         │
         │ HTTP
         ▼
┌─────────────────┐
│   Backend       │  :5000
│   (Flask API)   │  Python
└────────┬────────┘
         │
         │ ODBC
         ▼
┌─────────────────┐
│   Database      │  :1433
│   (MS SQL       │
│    Server)      │
└─────────────────┘
```

---

## Development vs Production

### Development
```bash
# Start with hot-reload
docker-compose -f docker-compose.dev.yml up
```

### Production
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Check database health
docker-compose ps

# View database logs
docker-compose logs database

# Restart database
docker-compose restart database
```

### Backend Not Starting
```bash
# View backend logs
docker-compose logs backend

# Check if database is ready
docker exec workhub-db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'WorkHub@2024!' -Q "SELECT 1"
```

### Frontend Build Errors
```bash
# Rebuild frontend
docker-compose build --no-cache frontend

# View frontend logs
docker-compose logs frontend
```

### Email Not Sending
1. Check `.env` file has correct credentials
2. Verify Gmail App Password (not regular password)
3. Check backend logs: `docker-compose logs backend`
4. Look for: "✓ Flask-Mail configured" message

---

## Database Management

### Backup Database
```bash
# Create backup
docker exec workhub-db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'WorkHub@2024!' \
  -Q "BACKUP DATABASE workhub TO DISK = '/var/opt/mssql/data/workhub.bak'"

# Copy backup to host
docker cp workhub-db:/var/opt/mssql/data/workhub.bak ./workhub-backup.bak
```

### Restore Database
```bash
# Copy backup to container
docker cp ./workhub-backup.bak workhub-db:/var/opt/mssql/data/

# Restore
docker exec workhub-db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'WorkHub@2024!' \
  -Q "RESTORE DATABASE workhub FROM DISK = '/var/opt/mssql/data/workhub-backup.bak' WITH REPLACE"
```

### Reset Database
```bash
# Only do this if you WANT a fresh, empty database.
docker-compose down
docker volume rm task_management_system-1_mssql_data
docker-compose up -d
```

---

## Security Considerations

### Production Deployment

1. **Change Default Passwords**
   - Database password in `docker-compose.yml`
   - Update SECRET_KEY and JWT_SECRET_KEY in `.env`

2. **Use Environment Variables**
   ```bash
   # Don't commit .env file
   echo ".env" >> .gitignore
   ```

3. **Enable HTTPS**
   - Use reverse proxy (nginx/traefik)
   - Configure SSL certificates
   - Update FRONTEND_URL to https

4. **Secure Database**
   - Use strong passwords
   - Limit network access
   - Enable encryption

5. **Monitor Logs**
   ```bash
   docker-compose logs -f --tail=100
   ```

---

## Performance Tuning

### For Production

1. **Scale Services**
   ```bash
   docker-compose up -d --scale backend=3
   ```

2. **Resource Limits**
   Edit `docker-compose.yml`:
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           cpus: '1'
           memory: 1G
   ```

3. **Database Optimization**
   - Increase SQL Server memory
   - Add indexes
   - Enable query caching

---

## Monitoring

### Health Checks
```bash
# Backend health
curl http://localhost:5000/api/health

# Database health
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100
```

---

## Updates and Maintenance

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Update Dependencies
```bash
# Backend
cd workhub-backend
pip freeze > requirements.txt

# Frontend
cd workhub-frontend
npm update

# Rebuild
docker-compose build --no-cache
```

---

## Support

For issues, check:
1. Docker logs: `docker-compose logs`
2. Application logs inside containers
3. Database connectivity
4. Email configuration

---

**Status**: Ready for Production ✅

Last Updated: 2025-10-27

