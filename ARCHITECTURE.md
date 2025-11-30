# School Portal Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          INTERNET                                │
│                     (Your Domain/IP)                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ HTTPS (443) / HTTP (80)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      YOUR VPS SERVER                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Docker Container: Nginx                   │ │
│  │  - Reverse Proxy                                          │ │
│  │  - SSL/TLS Termination                                    │ │
│  │  - Static/Media File Serving                             │ │
│  │  - Load Balancing (if scaled)                            │ │
│  └────────────┬───────────────────────────────┬──────────────┘ │
│               │                               │                  │
│               │ HTTP (8000)                   │ WebSocket        │
│               │                               │ (ws://)          │
│  ┌────────────▼──────────────────┐  ┌─────────▼───────────────┐│
│  │   Docker Container: Web       │  │  Django Channels (ASGI) ││
│  │   - Django 5.2.8              │  │  - Whiteboard WebSocket ││
│  │   - Django REST Framework     │  │  - Real-time Updates    ││
│  │   - Gunicorn (WSGI)           │  │                         ││
│  │   - 60+ API Endpoints         │  │                         ││
│  └──────┬────────────────────────┘  └─────────────────────────┘│
│         │                                                         │
│         │ SQL Queries                                            │
│         │                                                         │
│  ┌──────▼──────────────────────────────────────────────────────┐│
│  │          Docker Container: PostgreSQL 15                    ││
│  │  - Main Database (school_portal)                           ││
│  │  - User data, Homework, Classes, etc.                      ││
│  │  - Persistent Volume: postgres_data                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          Docker Container: Redis                          │  │
│  │  - Cache Layer                                            │  │
│  │  - Celery Message Broker                                  │  │
│  │  - WebSocket Channel Layer                                │  │
│  │  - Session Storage                                        │  │
│  └───────────┬───────────────────────────────────────────────┘  │
│              │                                                    │
│              │ Message Queue                                     │
│              │                                                    │
│  ┌───────────▼───────────────────────────────────────────────┐  │
│  │     Docker Container: Celery Worker (Phase 3)             │  │
│  │  - Background Tasks                                       │  │
│  │  - Email Sending                                          │  │
│  │  - Report Generation                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │     Docker Container: Celery Beat (Phase 3)               │  │
│  │  - Task Scheduler                                         │  │
│  │  - Homework Reminders (Daily 9 AM)                        │  │
│  │  - Parent Digests (Sunday 6 PM)                           │  │
│  │  - Session Cleanup (Daily 2 AM)                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Docker Volumes                          │  │
│  │  - postgres_data: Database persistence                    │  │
│  │  - redis_data: Redis persistence                          │  │
│  │  - media_files: User uploads                              │  │
│  │  - static_files: Static assets (CSS, JS)                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Request Flow
```
User Browser 
    → HTTPS Request 
    → Nginx (Port 443) 
    → Django Web (Port 8000)
    → PostgreSQL Database
    → Response back through same path
```

### 2. WebSocket Connection (Whiteboard)
```
User Browser 
    → WebSocket Connection (wss://)
    → Nginx WebSocket Proxy
    → Django Channels (ASGI)
    → Redis (Channel Layer)
    → Broadcast to all connected users
```

### 3. Background Task Flow
```
User Action (e.g., Homework Created)
    → Django View
    → Celery Task Queued (Redis)
    → Celery Worker Picks Up Task
    → Send Email/Process Data
    → Update Database
```

### 4. File Upload Flow
```
User Uploads File
    → Nginx (100MB limit)
    → Django File Handler
    → Saved to media_files Volume
    → Path stored in Database
    → Served by Nginx on request
```

## Network Architecture

```
┌────────────────────────────────────────────────────┐
│              Docker Network: school_network        │
│                                                    │
│  web:8000 ←→ db:5432                              │
│  web:8000 ←→ redis:6379                           │
│  celery_worker ←→ redis:6379                      │
│  celery_beat ←→ redis:6379                        │
│  nginx:80/443 ←→ web:8000                         │
│                                                    │
│  All containers communicate via internal network  │
│  Only Nginx exposed to internet (80/443)         │
└────────────────────────────────────────────────────┘
```

## Port Mapping

```
External Port → Container Port
──────────────────────────────
80  (HTTP)    → nginx:80
443 (HTTPS)   → nginx:443
8000          → web:8000 (optional, for direct access)

Internal Only:
──────────────
5432 → db:5432 (PostgreSQL)
6379 → redis:6379 (Redis)
```

## Security Layers

```
┌─────────────────────────────────────┐
│  1. Firewall (UFW)                  │
│     - Only 80, 443, 22 open         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  2. Nginx                           │
│     - SSL/TLS encryption            │
│     - Rate limiting                 │
│     - Request filtering             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  3. Django Middleware               │
│     - CSRF protection               │
│     - CORS validation               │
│     - Centre-based filtering        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  4. Authentication                  │
│     - JWT token validation          │
│     - Role-based permissions        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  5. Database                        │
│     - PostgreSQL access control     │
│     - Centre data isolation         │
└─────────────────────────────────────┘
```

## Scaling Options

### Horizontal Scaling
```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         │               │               │
      Web-1           Web-2           Web-3
         │               │               │
         └───────────────┼───────────────┘
                         │
                  Shared Resources
                 (DB, Redis, Storage)
```

### Vertical Scaling
```
Increase container resources:
- docker-compose.yml resource limits
- PostgreSQL max_connections
- Redis maxmemory
- Gunicorn workers
```

## Deployment Flow

```
1. Code on GitHub/GitLab
         │
         ▼
2. VPS Server (git pull)
         │
         ▼
3. docker-compose build
         │
         ▼
4. Build Images (Django, etc.)
         │
         ▼
5. docker-compose up -d
         │
         ▼
6. Containers Running
         │
         ▼
7. Run Migrations
         │
         ▼
8. Collect Static Files
         │
         ▼
9. Application Live! ✅
```

## Backup Strategy

```
Daily Automated Backups:
┌─────────────────────────────────────┐
│  Cron Job (2 AM)                    │
│    │                                │
│    ▼                                │
│  pg_dump → backup_YYYYMMDD.sql     │
│    │                                │
│    ▼                                │
│  Store in /backups/                 │
│    │                                │
│    ▼                                │
│  Keep last 7 days                   │
│  Delete older backups               │
└─────────────────────────────────────┘
```

## Monitoring Points

```
1. Application Logs
   - logs/django.log
   - docker-compose logs web

2. Database Performance
   - Connection count
   - Query performance

3. Redis Memory Usage
   - Used memory
   - Hit/miss ratio

4. Server Resources
   - CPU usage
   - RAM usage
   - Disk space

5. API Response Times
   - Average response time
   - Error rates
```

---

This architecture provides:
✅ High availability
✅ Scalability
✅ Security
✅ Performance
✅ Easy maintenance

