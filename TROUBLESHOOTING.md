# Deployment Lessons Learned & Troubleshooting

This document contains solutions to common issues encountered during deployment.

## Issues Encountered & Solutions

### Issue 1: Django Module Not Found in Container
**Error**: `ModuleNotFoundError: No module named 'django'`

**Root Cause**: The Dockerfile's multi-stage build was copying Python packages to `/root/.local` but the application runs as `appuser`, which doesn't have access to `/root/.local`.

**Solution**: 
- Copy packages to `/home/appuser/.local` instead
- Set PATH after switching to appuser: `ENV PATH=/home/appuser/.local/bin:$PATH`
- Fixed in [`Dockerfile`](Dockerfile) lines 37-41

### Issue 2: AttributeError - 'CharField' object has no attribute 'now'
**Error**: `AttributeError: 'CharField' object has no attribute 'now'`

**Root Cause**: In `apps/centres/models.py`, the model has a field named `timezone` which shadows the imported `timezone` module from `django.utils`.

**Solution**: 
- Rename the import: `from django.utils import timezone as django_timezone`
- Update all references: `timezone.now()` → `django_timezone.now()`
- Fixed in [`apps/centres/models.py`](apps/centres/models.py)

### Issue 3: Missing Migration Files
**Error**: `No changes detected` when running `makemigrations`

**Root Cause**: Migration directories (`migrations/`) didn't exist in the app folders.

**Solution**: 
- Create `migrations/__init__.py` in each app directory
- Run `python manage.py makemigrations` to generate migrations
- All migration directories now included in repository

### Issue 4: Permission Denied on .env File
**Error**: `cp: cannot create regular file '.env': Permission denied`

**Root Cause**: Project directory owned by root instead of the deployment user.

**Solution**:
```bash
sudo chown -R devops:devops /opt/MTO
```

### Issue 5: Nginx Keeps Restarting with SSL Redirect
**Error**: Nginx restarting, 301 redirects to HTTPS when no SSL configured

**Root Cause**: Default nginx configuration forces HTTPS redirect even without SSL certificates.

**Solution**: 
- Created HTTP-only configuration: [`nginx/conf.d/default.conf`](nginx/conf.d/default.conf)
- HTTPS configuration saved as example: [`nginx/conf.d/default-https.conf.example`](nginx/conf.d/default-https.conf.example)
- Update `.env`: `SECURE_SSL_REDIRECT=False`, `SESSION_COOKIE_SECURE=False`, `CSRF_COOKIE_SECURE=False`

### Issue 6: Docker Compose Version Warning
**Warning**: `the attribute 'version' is obsolete`

**Root Cause**: Docker Compose v2+ doesn't require version specification.

**Solution**: Removed `version: '3.8'` from [`docker-compose.yml`](docker-compose.yml)

## Pre-Deployment Checklist

### Required Files Check
```bash
# Verify all critical files exist
ls -la requirements.txt         # Python dependencies
ls -la Dockerfile              # Docker image
ls -la docker-compose.yml      # Container orchestration
ls -la manage.py               # Django management
ls -la config/settings.py      # Django settings
ls -la apps/users/models.py    # Custom user model
ls -la apps/*/migrations/      # Migration directories
ls -la nginx/conf.d/default.conf  # Nginx configuration
```

### Configuration Check
```bash
# Verify .env file settings
grep -E "SECRET_KEY|DEBUG|ALLOWED_HOSTS|DB_PASSWORD|REDIS_PASSWORD" .env

# Ensure SECRET_KEY is changed from default
# Ensure DEBUG=False for production
# Ensure passwords are strong and changed
```

### Permission Check
```bash
# Ensure proper ownership
ls -la /opt/MTO/backend | head -5

# Should show your user (e.g., devops) as owner
```

## Deployment Steps (Verified Working)

### Step 1: Fix Permissions
```bash
sudo chown -R devops:devops /opt/MTO
```

### Step 2: Create Environment File
```bash
cd /opt/MTO/backend
cp .env.example .env

# Generate SECRET_KEY
python3 -c 'import secrets; print("SECRET_KEY=" + secrets.token_urlsafe(50))'

# Edit .env with generated key and your settings
nano .env
```

### Step 3: Start Database and Redis Only
```bash
docker-compose up -d db redis
sleep 10
```

### Step 4: Generate and Apply Migrations
```bash
# Generate migrations
docker-compose run --rm web python manage.py makemigrations

# Apply migrations
docker-compose run --rm web python manage.py migrate
```

### Step 5: Start All Services
```bash
docker-compose up -d
sleep 15
```

### Step 6: Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### Step 7: Verify Deployment
```bash
# Check all containers are running
docker-compose ps

# Test API
curl http://localhost/api/health/
curl http://your-server-ip/api/health/

# Access in browser
# http://your-server-ip/admin/
# http://your-server-ip/swagger/
```

## Quick Commands Reference

```bash
# View logs in real-time
docker-compose logs -f web

# Restart specific service
docker-compose restart web
docker-compose restart nginx

# Rebuild after code changes
docker-compose up -d --build web

# Run Django commands
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py migrate

# Database backup
docker-compose exec db pg_dump -U postgres school_portal > backup.sql

# Database restore
docker-compose exec -T db psql -U postgres school_portal < backup.sql

# Stop all services
docker-compose down

# Clean restart
docker-compose down
docker-compose up -d --build
```

## Common Errors After Deployment

### Container Keeps Restarting
```bash
# Check logs immediately
docker-compose logs web | tail -50

# Common causes:
# - Migration not run
# - Database connection error
# - Import errors in Python code
```

### 502 Bad Gateway
```bash
# Web container not running or not healthy
docker-compose ps
docker-compose logs web

# Restart web
docker-compose restart web
```

### Static Files Not Loading
```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart nginx
```

### Database Connection Refused
```bash
# Check if database is running and healthy
docker-compose ps db
docker-compose logs db

# Verify credentials in .env match docker-compose.yml
```

## Performance Tips

### After First Successful Deployment
```bash
# Create database indexes (already in models)
docker-compose exec web python manage.py migrate

# Set up automated backups
crontab -e
# Add: 0 2 * * * docker-compose -f /opt/MTO/backend/docker-compose.yml exec -T db pg_dump -U postgres school_portal > /backups/school_portal_$(date +\%Y\%m\%d).sql
```

### Monitor Resources
```bash
# Check container resource usage
docker stats

# Check disk space
df -h

# Check logs size
du -sh logs/
```

## Security Hardening for Production

```bash
# 1. Generate strong passwords
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'

# 2. Update .env with strong passwords
nano .env

# 3. If using domain with SSL:
cp nginx/conf.d/default-https.conf.example nginx/conf.d/default.conf
# Edit with your domain
nano nginx/conf.d/default.conf

# 4. Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# 5. Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/*.pem nginx/ssl/

# 6. Update .env for HTTPS
nano .env
# Set: SECURE_SSL_REDIRECT=True
# Set: SESSION_COOKIE_SECURE=True
# Set: CSRF_COOKIE_SECURE=True
# Set: ALLOWED_HOSTS=your-domain.com
# Set: CSRF_TRUSTED_ORIGINS=https://your-domain.com

# 7. Restart
docker-compose restart
```

## Success Indicators

Your deployment is successful when:
- ✅ `docker-compose ps` shows all containers as "Up" or "healthy"
- ✅ `curl http://localhost/api/health/` returns `{"status":"ok"}`
- ✅ You can access `http://your-ip/admin/` in browser
- ✅ You can access `http://your-ip/swagger/` in browser
- ✅ You can login with superuser credentials
- ✅ No errors in `docker-compose logs web`

## Final Verification Commands

```bash
# Run these to verify everything works
cd /opt/MTO/backend

# 1. Check all containers
docker-compose ps

# 2. Test health endpoint
curl http://localhost/api/health/

# 3. Test API root
curl http://localhost/api/

# 4. Test admin (should get HTML)
curl -I http://localhost/admin/

# 5. Test Swagger
curl -I http://localhost/swagger/

# 6. Check logs for errors
docker-compose logs web | grep -i error | tail -20

# 7. Test database connection
docker-compose exec db psql -U postgres -d school_portal -c "SELECT COUNT(*) FROM auth_user;"
```

## What to Commit to Git

Include these:
- ✅ All source code (`apps/`, `config/`)
- ✅ Dockerfile
- ✅ docker-compose.yml
- ✅ requirements.txt
- ✅ nginx/ configuration (without ssl/ directory)
- ✅ Documentation (all .md files)
- ✅ .gitignore
- ✅ Migration directories (`apps/*/migrations/`)

Exclude these (already in .gitignore):
- ❌ .env (contains secrets)
- ❌ venv/ (virtual environment)
- ❌ *.pyc, __pycache__/
- ❌ media/ (user uploads)
- ❌ staticfiles/ (collected static)
- ❌ logs/ (application logs)
- ❌ db.sqlite3 (if using SQLite for dev)
- ❌ nginx/ssl/ (SSL certificates)
- ❌ nginx/logs/ (nginx logs)

## Timeline Summary

Total deployment time with troubleshooting: ~30 minutes
- Docker installation: 2 minutes
- Project setup: 5 minutes
- Troubleshooting: 15 minutes
- Migration and startup: 5 minutes
- Verification: 3 minutes

---

**All issues resolved! Application deployed successfully! ✅**

