# School Portal Backend - Deployment Guide

## Prerequisites on VPS

- Docker and Docker Compose installed
- Domain name pointed to your VPS IP
- Ports 80, 443, 5432, 6379 open in firewall

## Initial Setup on VPS

### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. Clone/Upload Project to VPS

```bash
# Option 1: Git clone (if using version control)
git clone your-repo-url school-portal
cd school-portal/backend

# Option 2: Upload via SCP from your local machine
# On your local machine:
scp -r backend/ user@your-vps-ip:/home/user/school-portal/
```

### 3. Configure Environment Variables

```bash
cd /path/to/school-portal/backend

# Copy environment template
cp .env.production .env

# Edit environment file with your settings
nano .env
```

**Important: Update these in .env file:**
- `SECRET_KEY` - Generate a strong random key
- `ALLOWED_HOSTS` - Your domain and IP
- `DB_PASSWORD` - Strong database password
- `REDIS_PASSWORD` - Strong Redis password
- `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` - Your email credentials
- `CSRF_TRUSTED_ORIGINS` - Your domain with https://

### 4. Configure Nginx

```bash
# Edit Nginx configuration
nano nginx/conf.d/default.conf

# Replace 'your-domain.com' with your actual domain
```

### 5. SSL Certificate Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Option 1: Stop containers temporarily and get certificate
docker-compose down
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to nginx/ssl directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl/

# Option 2: Use Certbot with Nginx (after containers are running)
# Update nginx/conf.d/default.conf to use self-signed cert first
# Then run: sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 6. Generate Django Secret Key

```bash
# Generate a secure secret key
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Copy the output and update SECRET_KEY in .env file
```

## Deployment Commands

### First Time Deployment

```bash
# Build and start containers
docker-compose up -d --build

# Wait for containers to be healthy
docker-compose ps

# Run database migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check logs
docker-compose logs -f web
```

### Subsequent Deployments

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Restart services
docker-compose restart web
```

## Management Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx
```

### Access Django Shell

```bash
docker-compose exec web python manage.py shell
```

### Access Database

```bash
# PostgreSQL shell
docker-compose exec db psql -U postgres -d school_portal

# Create database backup
docker-compose exec db pg_dump -U postgres school_portal > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T db psql -U postgres school_portal < backup_20231130.sql
```

### Stop/Start Services

```bash
# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Restart specific service
docker-compose restart web

# Rebuild specific service
docker-compose up -d --build web
```

### Scale Services (for production)

```bash
# Scale web workers
docker-compose up -d --scale web=3
```

## Phase 2 & 3 Deployment

### Enable Celery Workers (Phase 3)

```bash
# Start with celery services
docker-compose --profile phase3 up -d

# Or add celery services to default profile in docker-compose.yml
```

### Enable WebSocket Support (Phase 2)

The Django Channels configuration is already set up in nginx for WebSocket connections at `/ws/` endpoint.

## Monitoring and Maintenance

### Health Checks

```bash
# Check service health
docker-compose ps

# Check application health
curl http://your-domain.com/health/

# Check nginx status
docker-compose exec nginx nginx -t
```

### Update SSL Certificates

```bash
# Renew certificates (set up cron job)
sudo certbot renew --quiet

# Copy new certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
docker-compose restart nginx
```

### Automated Certificate Renewal (Cron)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 3am
0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /path/to/school-portal/backend/nginx/ssl/ && docker-compose -f /path/to/school-portal/backend/docker-compose.yml restart nginx
```

### Database Backup Automation

```bash
# Create backup script
nano backup.sh
```

Add this content:
```bash
#!/bin/bash
BACKUP_DIR="/home/user/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
docker-compose exec -T db pg_dump -U postgres school_portal > $BACKUP_DIR/school_portal_$DATE.sql
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

```bash
# Make executable
chmod +x backup.sh

# Add to crontab (daily at 2am)
0 2 * * * /path/to/school-portal/backend/backup.sh
```

## Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Performance Tuning

### PostgreSQL Configuration

Edit `docker-compose.yml` to add PostgreSQL parameters:

```yaml
db:
  command: postgres -c max_connections=200 -c shared_buffers=256MB -c effective_cache_size=1GB
```

### Redis Configuration

For production, use Redis persistent storage:

```yaml
redis:
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD} --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs web

# Check if ports are already in use
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :5432
```

### Database connection errors

```bash
# Restart database
docker-compose restart db

# Check database is ready
docker-compose exec db pg_isready -U postgres
```

### Permission errors

```bash
# Fix media/static permissions
docker-compose exec web chown -R appuser:appuser /app/media /app/staticfiles
```

### Nginx configuration errors

```bash
# Test nginx config
docker-compose exec nginx nginx -t

# Reload nginx
docker-compose exec nginx nginx -s reload
```

## Security Checklist

- [ ] Change all default passwords in .env
- [ ] Set DEBUG=False in production
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Enable automatic security updates
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Review ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
- [ ] Enable rate limiting in Django
- [ ] Set up monitoring and alerts

## Monitoring Setup (Optional)

### Install monitoring tools

```bash
# Prometheus and Grafana (for advanced monitoring)
# Add to docker-compose.yml or use external monitoring service
```

## Quick Commands Reference

```bash
# Deploy/Update
docker-compose up -d --build && docker-compose exec web python manage.py migrate

# View logs
docker-compose logs -f web

# Backup database
docker-compose exec db pg_dump -U postgres school_portal > backup.sql

# Restart all
docker-compose restart

# Clean up
docker system prune -a
```

## Support and Logs

All logs are stored in:
- Application logs: `docker-compose logs web`
- Nginx logs: `nginx/logs/`
- Database logs: `docker-compose logs db`

