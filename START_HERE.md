# 🚀 VPS Deployment - Quick Start Guide

## Overview
This guide will help you deploy the School Portal Django backend to your VPS in the fastest way possible.

---

## ⚡ Super Quick Deploy (5 Minutes)

### Prerequisites
- VPS with Ubuntu 20.04+ 
- Root/sudo access
- Domain name (optional)

### Steps

**1. Connect to your VPS:**
```bash
ssh root@your-vps-ip
```

**2. Upload your project:**
```bash
# Option A: Using Git (recommended)
git clone <your-repo-url> school-portal
cd school-portal/backend

# Option B: Using SCP from local machine
# On your local machine:
scp -r backend/ root@your-vps-ip:/root/school-portal/
# Then SSH to VPS:
ssh root@your-vps-ip
cd /root/school-portal/backend
```

**3. Configure environment:**
```bash
cp .env.production .env
nano .env
```

Edit these critical settings:
```bash
SECRET_KEY=<generate-a-random-key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-vps-ip
DB_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
```

Generate SECRET_KEY:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**4. Run automated deployment:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**5. Done! 🎉**

Access your portal:
- API: `http://your-vps-ip/api/`
- Admin: `http://your-vps-ip/admin/`
- Swagger: `http://your-vps-ip/swagger/`

---

## 📋 Detailed Steps (If You Want More Control)

### Step 1: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

### Step 2: Configure Firewall

```bash
sudo apt install ufw -y
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### Step 3: Set Up Environment

```bash
cd /root/school-portal/backend
cp .env.production .env
nano .env  # Edit with your settings
```

### Step 4: Deploy

```bash
docker-compose up -d --build
sleep 15  # Wait for services to start
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

### Step 5: Verify

```bash
# Check services
docker-compose ps

# Test API
curl http://localhost/api/health/

# View logs
docker-compose logs -f web
```

---

## 🔒 Set Up HTTPS/SSL (Recommended)

### Option 1: Let's Encrypt (Free, Production)

```bash
# Stop containers temporarily
docker-compose down

# Install Certbot
sudo apt install certbot -y

# Get certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy to nginx
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl/

# Restart
docker-compose up -d
```

### Option 2: Self-Signed (Testing Only)

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem
sudo chown -R $USER:$USER nginx/ssl/
docker-compose restart nginx
```

---

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f
docker-compose logs -f web
docker-compose logs -f db

# Restart services
docker-compose restart
docker-compose restart web

# Stop/Start
docker-compose down
docker-compose up -d

# Enter Django shell
docker-compose exec web python manage.py shell

# Backup database
docker-compose exec db pg_dump -U postgres school_portal > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres school_portal < backup.sql

# Update application
git pull origin main
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

---

## ⚙️ Enable Background Tasks (Phase 3)

```bash
# Start Celery workers
docker-compose --profile phase3 up -d

# Verify
docker-compose logs celery_worker
docker-compose logs celery_beat
```

---

## 📊 Monitoring

```bash
# Check container status
docker-compose ps

# View resource usage
docker stats

# Check disk space
df -h

# View application logs
docker-compose exec web tail -f logs/django.log
```

---

## 🐛 Troubleshooting

### Containers won't start
```bash
docker-compose logs
docker-compose down
docker-compose up -d
```

### Database connection error
```bash
docker-compose restart db
docker-compose exec web python manage.py migrate
```

### Nginx 502 error
```bash
docker-compose logs web
docker-compose restart web
```

### Static files not loading
```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart nginx
```

### Port already in use
```bash
sudo lsof -i :80
sudo lsof -i :443
# Stop the service using the port
```

---

## 📚 Documentation Files

- **`QUICK_DEPLOY.md`** ← You are here
- **`VPS_DEPLOYMENT_GUIDE.md`** - Comprehensive step-by-step guide
- **`DEPLOYMENT_CHECKLIST.md`** - Pre/post deployment checklist
- **`DEPLOYMENT.md`** - Technical deployment documentation
- **`SWAGGER_DOCUMENTATION.md`** - API documentation guide
- **`README.md`** - Project overview

---

## 🎯 Quick Reference

### Access Points
- **API Root**: `/api/`
- **Admin Panel**: `/admin/`
- **Swagger UI**: `/swagger/`
- **ReDoc**: `/redoc/`
- **Health Check**: `/api/health/`

### Default Ports
- HTTP: 80
- HTTPS: 443
- PostgreSQL: 5432 (internal)
- Redis: 6379 (internal)

### Important Files
- **Environment**: `.env`
- **Docker Config**: `docker-compose.yml`
- **Nginx Config**: `nginx/conf.d/default.conf`
- **Logs**: `logs/django.log`

---

## ✅ Post-Deployment Checklist

- [ ] Changed SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Updated ALLOWED_HOSTS
- [ ] Changed database password
- [ ] Configured SSL/HTTPS
- [ ] Set up firewall
- [ ] Tested API endpoints
- [ ] Created superuser
- [ ] Set up backups
- [ ] Configured email (optional)
- [ ] Enabled Celery (optional)

---

## 🆘 Need Help?

1. **Check logs**: `docker-compose logs -f`
2. **Review guides**: See documentation files above
3. **Test connections**: Use curl or browser
4. **Verify DNS**: Ensure domain points to VPS
5. **Check firewall**: Ensure ports 80/443 are open

---

## 🎓 What You've Deployed

✅ **60+ REST API endpoints**
✅ **Role-based access control** (5 roles)
✅ **Multi-centre support** with data isolation
✅ **Real-time whiteboard** (WebSocket)
✅ **Homework management** system
✅ **Calendar & events**
✅ **Analytics dashboard**
✅ **Email notifications** (optional)
✅ **Background tasks** (optional)
✅ **Interactive API docs** (Swagger)

---

## 🚀 Your Portal is Live!

**Production URL**: `https://your-domain.com`

**Next Steps:**
1. Login to admin panel: `/admin/`
2. Create centres, users, classes
3. Test homework submission flow
4. Try whiteboard functionality
5. Check Swagger documentation

**Congratulations! 🎉**

---

## 📧 Support

For deployment issues:
- Review logs: `docker-compose logs`
- Check documentation files
- Verify configuration in `.env`
- Test with curl commands

---

**Deployment Time: ~5-10 minutes** ⏱️
**Difficulty: Easy** ⭐
**Status: Production Ready** ✅

