# School Portal - Django Backend

A comprehensive multi-centre school management system with role-based access control, built with Django and Django REST Framework.

## Features

### Phase 1 - Core Features ✅
- **User Management**: Custom user model with 5 roles (Super Admin, Centre Manager, Teacher, Student, Parent)
- **Authentication**: JWT-based authentication with token refresh and account locking
- **Multi-Centre Support**: Full tenant isolation with centre-based data filtering
- **Centre Management**: Manage centres with holidays, term dates, and timezone support
- **Class Management**: Classes with teacher assignments and student enrolments
- **Homework System**: Create, assign, submit, and grade homework with file uploads
- **Calendar & Events**: Centre-wide and class-specific events with role-based visibility
- **Security**: Activity logging, permission classes, and audit trail

### Phase 2 - Enhanced Features ✅
- **Real-time Whiteboard**: WebSocket-based collaborative whiteboard using Django Channels
- **Dashboard APIs**: Role-specific dashboards for all user types
- **Parent Access**: Parent-student linking with filtered views
- **Student Profiles**: Extended profiles with sensitive data protection

### Phase 3 - Advanced Features ✅
- **Analytics Dashboard**: Homework trends, student performance, centre overview
- **Notification System**: Email notifications via Celery
- **Background Tasks**: Automated homework reminders, weekly parent digests
- **SMS Integration**: Twilio-based SMS notifications (optional)
- **Reporting**: Automated centre reports and performance metrics

## Technology Stack

- **Framework**: Django 5.2.8
- **API**: Django REST Framework 3.16.1
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL 15+
- **Real-time**: Django Channels 4.0 + Redis
- **Background Tasks**: Celery 5.3.4 + Redis
- **File Storage**: Django FileField (S3-ready)

## Project Structure

```
backend/
├── config/                     # Django project configuration
│   ├── settings.py            # Main settings file
│   ├── urls.py                # URL routing
│   ├── wsgi.py                # WSGI application
│   ├── asgi.py                # ASGI application (for WebSockets)
│   └── celery.py              # Celery configuration
├── apps/
│   ├── users/                 # User management & authentication
│   │   ├── models.py          # User, ActivityLog, ParentStudentLink, StudentProfile
│   │   ├── views.py           # Auth endpoints, user management
│   │   ├── serializers.py     # User serializers
│   │   └── admin.py           # Admin configuration
│   ├── centres/               # Centre management
│   │   ├── models.py          # Centre, Holiday, TermDate
│   │   ├── views.py           # Centre CRUD operations
│   │   └── serializers.py     # Centre serializers
│   ├── classes/               # Classes & enrolments
│   │   ├── models.py          # Class, TeacherAssignment, Enrolment
│   │   ├── views.py           # Class management
│   │   └── serializers.py     # Class serializers
│   ├── homework/              # Homework management
│   │   ├── models.py          # Homework, Submission
│   │   ├── views.py           # Homework CRUD, submission, grading
│   │   └── serializers.py     # Homework serializers
│   ├── calendar/              # Events & calendar
│   │   ├── models.py          # Event
│   │   ├── views.py           # Event management with visibility rules
│   │   └── serializers.py     # Event serializers
│   ├── whiteboard/            # Real-time whiteboard (Phase 2)
│   │   ├── models.py          # WhiteboardSession, WhiteboardSnapshot
│   │   ├── views.py           # Session management
│   │   ├── consumers.py       # WebSocket consumer
│   │   └── routing.py         # WebSocket routing
│   └── core/                  # Shared utilities
│       ├── permissions.py     # Custom permission classes
│       ├── middleware.py      # Centre filtering middleware
│       ├── dashboards.py      # Dashboard views for all roles
│       ├── analytics.py       # Analytics endpoints (Phase 3)
│       ├── tasks.py           # Celery tasks (Phase 3)
│       ├── mixins.py          # Reusable mixins
│       └── utils.py           # Helper functions
├── media/                     # User-uploaded files
├── staticfiles/               # Collected static files
├── logs/                      # Application logs
├── nginx/                     # Nginx configuration for deployment
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker image definition
└── manage.py                  # Django management script
```

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Login with email & password
- `POST /api/auth/logout/` - Logout (blacklist token)
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/password-reset/` - Request password reset

### Users
- `GET /api/users/` - List users (filtered by role)
- `POST /api/users/` - Create new user
- `GET /api/users/{id}/` - Get user details
- `PATCH /api/users/{id}/` - Update user
- `POST /api/users/change-password/` - Change password
- `GET /api/users/{id}/activity-logs/` - Get activity logs

### Centres
- `GET /api/centres/` - List centres
- `POST /api/centres/` - Create centre (Super Admin only)
- `GET /api/centres/{id}/` - Get centre details
- `GET /api/centres/{id}/holidays/` - Get/add holidays
- `GET /api/centres/{id}/terms/` - Get/add term dates

### Classes
- `GET /api/classes/` - List classes (filtered by centre)
- `POST /api/classes/` - Create class
- `GET /api/classes/{id}/` - Get class details
- `GET /api/classes/{id}/teachers/` - Manage teacher assignments
- `GET /api/classes/{id}/enrolments/` - Manage student enrolments

### Homework
- `GET /api/homework/` - List homework (role-based filtering)
- `POST /api/homework/` - Create homework (teachers only)
- `GET /api/homework/{id}/` - Get homework details
- `POST /api/homework/{id}/submit/` - Submit homework (students)
- `POST /api/homework/{id}/grade/{submission_id}/` - Grade submission (teachers)
- `GET /api/homework/{id}/submissions/` - List submissions

### Calendar
- `GET /api/events/` - List events (filtered by role & centre)
- `POST /api/events/` - Create event
- `GET /api/events/calendar/` - Calendar view (month/week/list)
- `GET /api/events/upcoming/` - Upcoming events (next 30 days)

### Whiteboard (Phase 2)
- `GET /api/whiteboard/sessions/` - List sessions
- `POST /api/whiteboard/sessions/` - Create session (teachers)
- `POST /api/whiteboard/sessions/{id}/join/` - Join session
- `POST /api/whiteboard/sessions/{id}/end/` - End session
- `GET /api/whiteboard/sessions/{id}/snapshots/` - Get/save snapshots
- `WS /ws/whiteboard/{id}/` - WebSocket connection for real-time collaboration

### Dashboards (Phase 2)
- `GET /api/dashboard/teacher/` - Teacher dashboard
- `GET /api/dashboard/student/` - Student dashboard
- `GET /api/dashboard/manager/` - Centre manager dashboard
- `GET /api/dashboard/parent/` - Parent dashboard

### Analytics (Phase 3)
- `GET /api/analytics/homework-trends/` - Homework submission trends
- `GET /api/analytics/student-performance/` - Student performance metrics
- `GET /api/analytics/centre-overview/` - Centre statistics
- `GET /api/analytics/teacher-performance/` - Teacher performance metrics

## Deployment

### Docker Deployment (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd backend
   ```

2. **Configure environment**:
   ```bash
   cp .env.production .env
   # Edit .env with your production settings
   ```

3. **Build and start containers**:
   ```bash
   docker-compose up -d --build
   ```

4. **Run migrations**:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create superuser**:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the application**:
   - API: `http://your-domain.com/api/`
   - Admin: `http://your-domain.com/admin/`

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Local Development

1. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.local .env
   # Edit .env with local settings
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**:
   ```bash
   python manage.py runserver
   ```

### Phase 2 & 3 Additional Setup

**For Whiteboard (Phase 2):**
- Redis must be running for WebSocket support
- Use Daphne or Uvicorn for ASGI server in production

**For Celery (Phase 3):**
```bash
# Start Celery worker
celery -A config worker -l info

# Start Celery beat (for scheduled tasks)
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Role-Based Access Control

### Super Admin
- Full access to all centres and data
- Manage global settings and permissions
- View all reports and analytics

### Centre Manager
- Access to their assigned centre only
- Manage classes, teachers, and students
- View full student profiles
- Create centre events and holidays
- Access centre-level analytics

### Teacher
- Access to assigned classes only
- Create and manage homework
- Grade submissions
- Create class events
- Start whiteboard sessions
- View student names only (not full profiles)

### Student
- View homework for enrolled classes
- Submit homework assignments
- Join whiteboard sessions
- View centre events and class events
- Access personal dashboard

### Parent
- View linked students' information
- Monitor homework and grades
- View events for linked students
- Receive weekly progress digests

## Security Features

- JWT authentication with refresh tokens
- Account locking after 5 failed login attempts
- Activity logging for sensitive actions
- Role-based permission system
- Centre-based data isolation
- Password validation and hashing
- HTTPS enforcement in production
- CORS protection
- CSRF protection

## Testing

Run tests with pytest:
```bash
pytest
```

Coverage report:
```bash
pytest --cov=apps --cov-report=html
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `/swagger/` or `/api-docs/` (interactive, try endpoints)
- **ReDoc**: `/redoc/` (clean documentation view)
- **OpenAPI Schema**: `/swagger.json` or `/swagger.yaml`

### Using Swagger UI

1. Navigate to `https://your-domain.com/swagger/`
2. Click "Authorize" and enter: `Bearer <your-access-token>`
3. Try out any endpoint interactively
4. See request/response examples for all endpoints

For detailed instructions, see [SWAGGER_DOCUMENTATION.md](SWAGGER_DOCUMENTATION.md)

## Performance Considerations

- Database indexing on frequently queried fields
- Query optimization with `select_related` and `prefetch_related`
- Pagination on list endpoints (20 items per page)
- Redis caching for dashboard data
- Background task processing with Celery

## Monitoring & Logging

- Application logs: `logs/django.log`
- Celery logs: Container logs
- Database logs: PostgreSQL logs
- Activity logs: Stored in database (`ActivityLog` model)

## Support & Troubleshooting

For issues and questions:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common deployment issues and solutions
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions
- Review [GIT_PREPARATION.md](GIT_PREPARATION.md) for Git upload guide
- Review API documentation at `/swagger/`
- Check application logs: `docker-compose logs web`

## License

Proprietary - All rights reserved

---

**Note**: This backend is designed to be deployed with Docker on a VPS. All Phase 1, 2, and 3 features are fully implemented and ready for deployment.
