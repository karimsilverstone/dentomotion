# Quick Deploy Instructions

## Fastest Way to Deploy on VPS

### Method 1: Automated Script (Recommended)

```bash
# 1. Connect to VPS
ssh your-username@your-vps-ip

# 2. Upload/clone your project
git clone <your-repo> school-portal
cd school-portal/backend

# 3. Make deploy script executable
chmod +x deploy.sh

# 4. Edit .env file (IMPORTANT!)
nano .env
# Change SECRET_KEY, passwords, domain, etc.

# 5. Run deployment script
./deploy.sh

# That's it! The script will:
# - Install Docker & Docker Compose
# - Configure firewall
# - Build containers
# - Run migrations
# - Collect static files
# - Create superuser
```

### Method 2: Manual Steps

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Configure environment
cd /path/to/backend
cp .env.production .env
nano .env  # Edit with your settings

# 4. Deploy
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

### Method 3: Using Git

```bash
# On VPS
cd ~
git clone https://github.com/your-username/school-portal.git
cd school-portal/backend
cp .env.production .env
nano .env  # Edit settings
chmod +x deploy.sh
./deploy.sh
```

## Essential .env Settings

**Must change these:**
```bash
SECRET_KEY=<generate-random-key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-ip
DB_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
```

**Generate SECRET_KEY:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## SSL Certificate (HTTPS)

```bash
# Install Certbot
sudo apt install certbot -y

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy to nginx
sudo cp /etc/letsencrypt/live/your-domain.com/*.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl/

# Restart Nginx
docker-compose restart nginx
```

## Quick Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all
docker-compose down

# Start all
docker-compose up -d

# Backup database
docker-compose exec db pg_dump -U postgres school_portal > backup.sql
```

## Verify Deployment

```bash
# Test health
curl http://your-domain.com/api/health/

# Check containers
docker-compose ps

# View logs
docker-compose logs web
```

## Access Your Portal

- API: `https://your-domain.com/api/`
- Admin: `https://your-domain.com/admin/`
- Swagger: `https://your-domain.com/swagger/`

## Troubleshooting

**Containers won't start:**
```bash
docker-compose logs
```

**Database connection error:**
```bash
docker-compose restart db
docker-compose exec web python manage.py migrate
```

**Port already in use:**
```bash
sudo lsof -i :80
sudo lsof -i :443
# Kill the process or stop the service
```

## Need Help?

See detailed guides:
- `VPS_DEPLOYMENT_GUIDE.md` - Complete step-by-step guide
- `DEPLOYMENT_CHECKLIST.md` - Pre/post deployment checklist
- `DEPLOYMENT.md` - Technical deployment details

---

**Deploy in 5 Minutes! 🚀**

