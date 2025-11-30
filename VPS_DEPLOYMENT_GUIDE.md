# Complete VPS Deployment Guide - School Portal

This guide will walk you through deploying the School Portal Django backend on your VPS from scratch.

## Prerequisites

- VPS with Ubuntu 20.04+ (or similar Linux distribution)
- Root or sudo access
- Domain name pointed to your VPS IP (optional but recommended)
- SSH access to your VPS

## Step-by-Step Deployment

### Step 1: Connect to Your VPS

```bash
ssh root@your-vps-ip
# or
ssh your-username@your-vps-ip
```

### Step 2: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 3: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (optional, to run docker without sudo)
sudo usermod -aG docker $USER

# Verify Docker installation
docker --version
```

### Step 4: Install Docker Compose

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### Step 5: Upload Your Project to VPS

**Option A: Using Git (Recommended)**

```bash
# Install git if not already installed
sudo apt install git -y

# Clone your repository
cd /home/$USER
git clone https://github.com/your-username/your-repo.git school-portal
cd school-portal/backend
```

**Option B: Using SCP from your local machine**

```bash
# On your LOCAL machine (not VPS)
# Navigate to your project directory
cd D:\Projects\MTO

# Upload to VPS
scp -r backend/ your-username@your-vps-ip:/home/your-username/school-portal/

# Then on VPS
ssh your-username@your-vps-ip
cd /home/your-username/school-portal/backend
```

**Option C: Using SFTP/FTP Client**
- Use FileZilla, WinSCP, or similar
- Connect to your VPS
- Upload the entire `backend` folder

### Step 6: Configure Environment Variables

```bash
cd /home/$USER/school-portal/backend

# Copy the production environment template
cp .env.production .env

# Edit the environment file
nano .env
```

**Critical settings to change in .env:**

```bash
# Django Settings - CHANGE THESE!
SECRET_KEY=GENERATE_A_STRONG_RANDOM_KEY_HERE
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-vps-ip

# Database - CHANGE PASSWORD!
DB_NAME=school_portal
DB_USER=postgres
DB_PASSWORD=CHANGE_THIS_TO_STRONG_PASSWORD

# JWT Settings (can keep defaults)
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Email Settings (configure your SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis
REDIS_URL=redis://:redis123@redis:6379/0
REDIS_PASSWORD=CHANGE_THIS_PASSWORD

# Security
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

**To generate a strong SECRET_KEY:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Save the file (Ctrl+X, then Y, then Enter in nano).

### Step 7: Configure Domain (If Using)

**Update Nginx configuration:**

```bash
nano nginx/conf.d/default.conf
```

Replace all instances of `your-domain.com` with your actual domain name.

**Point your domain to VPS:**
- Go to your domain registrar (Namecheap, GoDaddy, etc.)
- Add an A record pointing to your VPS IP address
- Wait for DNS propagation (5-30 minutes)

### Step 8: Set Up SSL Certificate (HTTPS)

**Option A: Using Let's Encrypt (Free, Recommended)**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Stop any services on port 80/443
docker-compose down

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl/
```

**Option B: Using Self-Signed Certificate (For Testing)**

```bash
# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem

sudo chown -R $USER:$USER nginx/ssl/
```

### Step 9: Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status
```

### Step 10: Build and Start Docker Containers

```bash
cd /home/$USER/school-portal/backend

# Build and start all services
docker-compose up -d --build

# This will take several minutes...
# Wait for all containers to start
```

### Step 11: Run Database Migrations

```bash
# Wait a few seconds for database to be ready
sleep 10

# Run migrations
docker-compose exec web python manage.py migrate

# You should see output like:
# Operations to perform:
#   Apply all migrations: admin, auth, calendar, centres, classes, ...
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   ...
```

### Step 12: Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser

# You'll be prompted for:
# Email address: admin@yourschool.com
# First name: Admin
# Last name: User
# Role (SUPER_ADMIN/CENTRE_MANAGER/TEACHER/STUDENT/PARENT): SUPER_ADMIN
# Password: ********
# Password (again): ********
```

### Step 13: Collect Static Files

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Step 14: Verify Deployment

```bash
# Check all containers are running
docker-compose ps

# You should see:
# - school_portal_db (healthy)
# - school_portal_redis (healthy)
# - school_portal_web (healthy)
# - school_portal_nginx (running)

# Check logs
docker-compose logs -f web

# Press Ctrl+C to exit logs
```

### Step 15: Test Your API

**From your browser or using curl:**

```bash
# Test health endpoint
curl https://your-domain.com/api/health/

# Should return: {"status":"ok"}

# Test API root
curl https://your-domain.com/api/

# Visit Swagger documentation
# Open browser: https://your-domain.com/swagger/

# Visit Admin panel
# Open browser: https://your-domain.com/admin/
```

### Step 16: Enable Celery (Phase 3 - Optional)

If you want background tasks (email notifications, etc.):

```bash
# Start with Phase 3 profile
docker-compose --profile phase3 up -d

# Verify Celery is running
docker-compose logs celery_worker
docker-compose logs celery_beat
```

## Post-Deployment Tasks

### 1. Set Up Automated Backups

Create backup script:

```bash
nano /home/$USER/backup.sh
```

Add this content:

```bash
#!/bin/bash
BACKUP_DIR="/home/$USER/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f /home/$USER/school-portal/backend/docker-compose.yml exec -T db pg_dump -U postgres school_portal > $BACKUP_DIR/school_portal_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: school_portal_$DATE.sql"
```

Make it executable:

```bash
chmod +x /home/$USER/backup.sh
```

Schedule daily backups:

```bash
crontab -e

# Add this line (runs daily at 2 AM):
0 2 * * * /home/$USER/backup.sh
```

### 2. Set Up SSL Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Add auto-renewal to crontab
crontab -e

# Add this line (checks twice daily):
0 0,12 * * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /home/$USER/school-portal/backend/nginx/ssl/ && docker-compose -f /home/$USER/school-portal/backend/docker-compose.yml restart nginx
```

### 3. Monitor Logs

```bash
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx

# View Django application logs
docker-compose exec web tail -f logs/django.log
```

## Common Issues and Solutions

### Issue 1: Containers Won't Start

```bash
# Check logs
docker-compose logs

# Common causes:
# - Port already in use (stop other services)
# - Permission issues (check file ownership)
# - Database connection (check DB credentials in .env)
```

### Issue 2: Database Connection Error

```bash
# Check database is running
docker-compose ps db

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Issue 3: Nginx 502 Bad Gateway

```bash
# Check web container is running
docker-compose ps web

# Check web logs
docker-compose logs web

# Restart web container
docker-compose restart web
```

### Issue 4: SSL Certificate Issues

```bash
# Check certificate files exist
ls -la nginx/ssl/

# Check Nginx configuration
docker-compose exec nginx nginx -t

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

### Issue 5: Static Files Not Loading

```bash
# Collect static files again
docker-compose exec web python manage.py collectstatic --noinput

# Restart Nginx
docker-compose restart nginx
```

## Updating Your Application

```bash
# Pull latest changes (if using git)
cd /home/$USER/school-portal/backend
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Run new migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## Stopping/Starting Services

```bash
# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Restart specific service
docker-compose restart web

# Restart all services
docker-compose restart
```

## Useful Commands

```bash
# Enter Django shell
docker-compose exec web python manage.py shell

# Enter database shell
docker-compose exec db psql -U postgres school_portal

# View running processes
docker-compose ps

# View resource usage
docker stats

# Clean up old images
docker system prune -a
```

## Security Checklist

- [x] Changed SECRET_KEY
- [x] Set DEBUG=False
- [x] Changed database password
- [x] Changed Redis password
- [x] Configured firewall
- [x] Set up HTTPS/SSL
- [x] Configured CORS properly
- [x] Set up backups
- [x] Configured email for notifications
- [ ] Set up monitoring (optional)
- [ ] Configure fail2ban (optional)

## Accessing Your Application

- **API**: https://your-domain.com/api/
- **Admin**: https://your-domain.com/admin/
- **Swagger**: https://your-domain.com/swagger/
- **ReDoc**: https://your-domain.com/redoc/

## Getting Help

If you encounter issues:
1. Check logs: `docker-compose logs`
2. Review error messages
3. Check environment variables in .env
4. Verify domain DNS is pointing correctly
5. Ensure firewall allows ports 80 and 443

---

**Congratulations! Your School Portal is now live! 🎉**

