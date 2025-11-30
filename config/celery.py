"""
Celery configuration for School Portal
Handles background tasks like email notifications, SMS, and scheduled reports
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('school_portal')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule (for periodic tasks)
app.conf.beat_schedule = {
    'send-homework-reminders-daily': {
        'task': 'apps.core.tasks.send_homework_reminders',
        'schedule': crontab(hour=9, minute=0),  # Every day at 9 AM
    },
    'send-weekly-parent-digest': {
        'task': 'apps.core.tasks.send_weekly_parent_digest',
        'schedule': crontab(day_of_week='sunday', hour=18, minute=0),  # Every Sunday at 6 PM
    },
    'cleanup-old-whiteboard-sessions': {
        'task': 'apps.core.tasks.cleanup_old_sessions',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

