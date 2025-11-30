# Deployment Checklist for School Portal Backend

## Pre-Deployment Checklist

### 1. Environment Configuration
- [ ] Copy `.env.production` to `.env` and configure all variables
- [ ] Set strong `SECRET_KEY` (use Django's `get_random_secret_key()`)
- [ ] Configure `ALLOWED_HOSTS` with your domain/IP
- [ ] Set `DEBUG=False` for production
- [ ] Configure database credentials (`DB_NAME`, `DB_USER`, `DB_PASSWORD`)
- [ ] Set up email configuration (SMTP settings)
- [ ] Configure Redis URL for caching and Celery
- [ ] Set `CSRF_TRUSTED_ORIGINS` with your domain(s)
- [ ] Optional: Configure AWS S3 for file storage
- [ ] Optional: Configure Twilio for SMS notifications

### 2. Server Setup
- [ ] Install Docker and Docker Compose on VPS
- [ ] Open required ports (80, 443) in firewall
- [ ] Configure domain DNS to point to VPS IP
- [ ] Install and configure SSL certificates (Let's Encrypt)
- [ ] Set up automatic backups for PostgreSQL database

### 3. Docker Configuration
- [ ] Review `docker-compose.yml` for production settings
- [ ] Update Nginx configuration in `nginx/conf.d/default.conf`
- [ ] Replace `your-domain.com` with actual domain
- [ ] Place SSL certificates in `nginx/ssl/` directory
- [ ] Adjust resource limits if needed (memory, CPU)

### 4. Database Setup
- [ ] PostgreSQL is configured in docker-compose
- [ ] Database credentials match `.env` file
- [ ] Consider increasing PostgreSQL max_connections for production
- [ ] Set up automated daily backups
- [ ] Test database connection before deployment

### 5. Security Hardening
- [ ] Change all default passwords
- [ ] Enable firewall (ufw) and allow only necessary ports
- [ ] Configure fail2ban for SSH protection
- [ ] Review and update CORS settings
- [ ] Enable HTTPS redirect in Nginx
- [ ] Set secure cookie flags (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)
- [ ] Review permission classes and access control

## Deployment Steps

### Step 1: Upload Project to VPS
```bash
# From your local machine
scp -r backend/ user@your-vps-ip:/home/user/school-portal/

# Or use git
ssh user@your-vps-ip
cd /home/user
git clone <your-repo> school-portal
cd school-portal/backend
```

### Step 2: Configure Environment
```bash
cd /home/user/school-portal/backend
cp .env.production .env
nano .env  # Edit with your settings
```

### Step 3: Build and Start Containers
```bash
docker-compose up -d --build
```

### Step 4: Run Migrations
```bash
docker-compose exec web python manage.py migrate
```

### Step 5: Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### Step 6: Collect Static Files
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Step 7: Verify Services
```bash
# Check all containers are running
docker-compose ps

# Check logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx
```

### Step 8: Test API
```bash
# Test health endpoint
curl https://your-domain.com/api/health/

# Test admin login
# Visit https://your-domain.com/admin/
```

## Phase 2 Deployment (Whiteboard)

### Additional Steps:
- [ ] Redis is running (included in docker-compose)
- [ ] Django Channels is configured (already done)
- [ ] WebSocket endpoint is accessible
- [ ] Test whiteboard connection: `ws://your-domain.com/ws/whiteboard/`

## Phase 3 Deployment (Background Tasks)

### Celery Setup:
```bash
# Start Celery services with Phase 3 profile
docker-compose --profile phase3 up -d

# Verify Celery worker is running
docker-compose logs -f celery_worker

# Verify Celery beat is running
docker-compose logs -f celery_beat
```

### Email Configuration:
- [ ] SMTP settings are correct in `.env`
- [ ] Test email sending with Django shell
- [ ] Verify homework reminders are scheduled

### SMS Configuration (Optional):
- [ ] Twilio credentials configured in `.env`
- [ ] Test SMS sending functionality

## Post-Deployment Verification

### 1. Functional Tests
- [ ] Login as each role (Super Admin, Manager, Teacher, Student, Parent)
- [ ] Create a centre and add users
- [ ] Create classes and assign teachers
- [ ] Enrol students in classes
- [ ] Create and submit homework
- [ ] Grade homework
- [ ] Create calendar events
- [ ] Start and join whiteboard session
- [ ] Check dashboard for each role
- [ ] Verify analytics endpoints (Manager/Admin)
- [ ] Test parent-student linking

### 2. Performance Tests
- [ ] API response times are acceptable
- [ ] Database queries are optimized
- [ ] File uploads work correctly
- [ ] WebSocket connections are stable
- [ ] Page load times are fast

### 3. Security Tests
- [ ] HTTPS is enforced
- [ ] API authentication works correctly
- [ ] Role-based permissions are enforced
- [ ] Centre data isolation is working
- [ ] File upload restrictions are enforced
- [ ] SQL injection protection is active
- [ ] XSS protection is enabled

### 4. Monitoring Setup
- [ ] Set up log monitoring (e.g., Sentry)
- [ ] Configure server monitoring (CPU, RAM, disk)
- [ ] Set up uptime monitoring
- [ ] Configure backup verification
- [ ] Set up alerts for errors

## Backup Strategy

### Database Backups
```bash
# Manual backup
docker-compose exec db pg_dump -U postgres school_portal > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T db psql -U postgres school_portal < backup_20240101.sql
```

### Automated Backups
Add to crontab:
```bash
0 2 * * * /home/user/school-portal/backend/backup.sh
```

### Backup Script (`backup.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/home/user/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U postgres school_portal > $BACKUP_DIR/school_portal_$DATE.sql
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

## Maintenance Tasks

### Daily
- [ ] Monitor application logs
- [ ] Check disk space
- [ ] Verify backups completed

### Weekly
- [ ] Review security logs
- [ ] Check for updates (Django, packages)
- [ ] Review performance metrics
- [ ] Test backup restoration

### Monthly
- [ ] Update packages (security patches)
- [ ] Review and optimize database
- [ ] Clean up old sessions and logs
- [ ] Review user access and permissions

## Rollback Plan

### If Deployment Fails:
1. Stop containers: `docker-compose down`
2. Restore previous configuration
3. Restore database backup if needed
4. Restart with previous version
5. Investigate logs to identify issue

### Database Rollback:
```bash
# Stop services
docker-compose down

# Restore database
docker-compose up -d db
docker-compose exec -T db psql -U postgres school_portal < backup_previous.sql

# Restart services
docker-compose up -d
```

## Support & Troubleshooting

### Common Issues:

**Container won't start:**
```bash
docker-compose logs web
# Check environment variables
# Verify database connection
```

**Database connection error:**
```bash
# Verify database container is running
docker-compose ps db
# Check database credentials in .env
```

**Static files not loading:**
```bash
# Collect static files again
docker-compose exec web python manage.py collectstatic --noinput
# Check Nginx configuration
```

**WebSocket not connecting:**
```bash
# Verify Redis is running
docker-compose ps redis
# Check Nginx WebSocket configuration
# Verify ASGI application is running
```

**Celery tasks not running:**
```bash
# Check Celery worker logs
docker-compose logs celery_worker
# Verify Redis connection
# Check beat schedule configuration
```

## Performance Optimization

### Database Optimization:
```sql
-- Run in PostgreSQL
ANALYZE;
VACUUM ANALYZE;

-- Add indexes if needed (already included in models)
```

### Redis Configuration:
- Adjust `maxmemory` based on server resources
- Use `allkeys-lru` eviction policy
- Monitor Redis memory usage

### Nginx Optimization:
- Enable gzip compression (already configured)
- Set appropriate cache headers
- Optimize worker_processes for your server

## Scaling Considerations

### Horizontal Scaling:
- Use Docker Swarm or Kubernetes
- Add load balancer (Nginx, HAProxy)
- Configure shared file storage (NFS, S3)
- Use external Redis cluster

### Vertical Scaling:
- Increase container resource limits
- Optimize PostgreSQL configuration
- Add more Celery workers

## Contact & Support

For deployment assistance:
- Review DEPLOYMENT.md for detailed instructions
- Check application logs: `docker-compose logs`
- Review this checklist for missed steps

---

**Important**: Always test deployments in a staging environment before production!

