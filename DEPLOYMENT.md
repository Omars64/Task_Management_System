# Work Hub Deployment Guide

This guide covers multiple deployment options for the Work Hub Task Management System.

## Quick Start (Docker - Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Steps

1. **Clone/Navigate to the project**
   ```bash
   cd /workspace
   ```

2. **Run setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:5000/api

### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild containers
docker-compose up -d --build
```

## Manual Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- MySQL 8.0+

### Steps

1. **Run manual setup script**
   ```bash
   chmod +x setup-manual.sh
   ./setup-manual.sh
   ```

2. **Start Backend** (Terminal 1)
   ```bash
   cd workhub-backend
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   python app.py
   ```

3. **Start Frontend** (Terminal 2)
   ```bash
   cd workhub-frontend
   npm run dev
   ```

## Production Deployment

### Option 1: Docker Production

1. **Update docker-compose.yml** for production:
   ```yaml
   backend:
     environment:
       FLASK_ENV: production
       SECRET_KEY: <strong-random-key>
       JWT_SECRET_KEY: <strong-random-key>
   ```

2. **Use production builds**:
   ```bash
   # Build frontend for production
   cd workhub-frontend
   npm run build
   ```

3. **Add nginx reverse proxy** (recommended)

### Option 2: Traditional Server Deployment

#### Backend Deployment

1. **Install dependencies**
   ```bash
   cd workhub-backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt gunicorn
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Initialize database**
   ```bash
   python init_db.py
   ```

4. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
   ```

5. **Set up systemd service** (Linux)
   ```bash
   sudo nano /etc/systemd/system/workhub-backend.service
   ```

   ```ini
   [Unit]
   Description=Work Hub Backend
   After=network.target mysql.service

   [Service]
   User=www-data
   WorkingDirectory=/var/www/workhub-backend
   Environment="PATH=/var/www/workhub-backend/venv/bin"
   ExecStart=/var/www/workhub-backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:create_app()
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   sudo systemctl enable workhub-backend
   sudo systemctl start workhub-backend
   ```

#### Frontend Deployment

1. **Build for production**
   ```bash
   cd workhub-frontend
   npm install
   npm run build
   ```

2. **Serve with nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/workhub
   ```

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       # Frontend
       location / {
           root /var/www/workhub-frontend/dist;
           try_files $uri $uri/ /index.html;
       }

       # Backend API
       location /api {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   ```bash
   sudo ln -s /etc/nginx/sites-available/workhub /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Configure SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### Option 3: Cloud Deployment

#### AWS Deployment

1. **RDS for MySQL**
   - Create RDS MySQL instance
   - Update backend .env with RDS credentials

2. **EC2 for Backend**
   - Launch EC2 instance
   - Install dependencies
   - Deploy backend with systemd + nginx

3. **S3 + CloudFront for Frontend**
   - Build frontend: `npm run build`
   - Upload dist/ to S3
   - Configure CloudFront distribution
   - Update API endpoint in frontend

#### Heroku Deployment

**Backend:**
```bash
cd workhub-backend
heroku create workhub-backend
heroku addons:create cleardb:ignite
heroku config:set SECRET_KEY=<your-secret>
heroku config:set JWT_SECRET_KEY=<your-jwt-secret>
git push heroku main
```

**Frontend:**
```bash
cd workhub-frontend
# Update API URL in vite.config.js
heroku create workhub-frontend
git push heroku main
```

#### DigitalOcean App Platform

1. Create new app from GitHub repository
2. Configure build settings:
   - Backend: Python with gunicorn
   - Frontend: Node.js with npm run build
3. Add MySQL database
4. Set environment variables

## Database Migration

### Backup Database
```bash
mysqldump -u root -p workhub > backup.sql
```

### Restore Database
```bash
mysql -u root -p workhub < backup.sql
```

### Migration to Production DB
1. Update .env with production DB credentials
2. Run `python init_db.py` to create schema
3. Import existing data if needed

## Environment Variables

### Backend (.env)
```bash
FLASK_ENV=production
SECRET_KEY=<strong-random-key-min-32-chars>
JWT_SECRET_KEY=<strong-random-key-min-32-chars>

DB_HOST=your-db-host
DB_PORT=3306
DB_NAME=workhub
DB_USER=your-db-user
DB_PASSWORD=your-db-password

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

FRONTEND_URL=https://your-domain.com
```

### Frontend (vite.config.js)
Update API proxy for production:
```javascript
server: {
  proxy: {
    '/api': {
      target: 'https://your-backend-domain.com',
      changeOrigin: true
    }
  }
}
```

## Security Checklist

- [ ] Change default SECRET_KEY and JWT_SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Keep dependencies updated
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up monitoring and logging

## Monitoring

### Application Logs

**Backend:**
```bash
# Docker
docker-compose logs -f backend

# Systemd
sudo journalctl -u workhub-backend -f
```

**Frontend:**
```bash
# Docker
docker-compose logs -f frontend

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Database Monitoring
```bash
# Check MySQL status
docker-compose exec mysql mysql -u root -p -e "SHOW PROCESSLIST;"

# Check database size
docker-compose exec mysql mysql -u root -p -e "SELECT table_schema AS 'Database', ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)' FROM information_schema.TABLES GROUP BY table_schema;"
```

## Performance Optimization

1. **Enable Gzip Compression** (nginx)
   ```nginx
   gzip on;
   gzip_types text/plain text/css application/json application/javascript;
   ```

2. **Database Indexing**
   - Already configured in models.py
   - Monitor slow queries

3. **Caching**
   - Add Redis for session storage
   - Cache frequent queries

4. **CDN**
   - Use CDN for static assets
   - CloudFront, Cloudflare, etc.

## Troubleshooting

### Database Connection Failed
```bash
# Check MySQL is running
docker-compose ps
# or
sudo systemctl status mysql

# Test connection
mysql -h DB_HOST -u DB_USER -p
```

### Backend Not Starting
```bash
# Check logs
docker-compose logs backend

# Check dependencies
pip list

# Verify environment variables
env | grep DB_
```

### Frontend Build Errors
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

## Scaling

### Horizontal Scaling

1. **Load Balancer** - nginx or cloud load balancer
2. **Multiple Backend Instances** - Run multiple gunicorn workers
3. **Database Replication** - MySQL master-slave setup
4. **Session Storage** - Use Redis for shared sessions

### Vertical Scaling

1. Increase server resources (CPU, RAM)
2. Optimize database queries
3. Add database indexes
4. Use connection pooling

## Backup Strategy

### Automated Backups

```bash
# Create backup script
cat > /usr/local/bin/backup-workhub.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backups/workhub
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u root -p$DB_PASSWORD workhub > $BACKUP_DIR/workhub_$DATE.sql
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-workhub.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /usr/local/bin/backup-workhub.sh
```

## Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test database connection
4. Review nginx/gunicorn configuration
5. Check firewall rules

---

Happy Deploying! 🚀