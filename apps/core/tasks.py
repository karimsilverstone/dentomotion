"""
Celery tasks for notifications and background jobs
"""
from celery import shared_task
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from apps.homework.models import Homework, Submission
from apps.users.models import User, ParentStudentLink
from apps.classes.models import Enrolment
from apps.whiteboard.models import WhiteboardSession


@shared_task
def send_homework_reminder_email(homework_id):
    """Send reminder email to students about upcoming homework"""
    try:
        homework = Homework.objects.get(id=homework_id)
        
        # Get enrolled students
        enrolments = Enrolment.objects.filter(
            class_instance=homework.class_instance,
            is_active=True
        ).select_related('student')
        
        for enrolment in enrolments:
            student = enrolment.student
            
            # Check if already submitted
            submission = Submission.objects.filter(
                homework=homework,
                student=student
            ).first()
            
            if not submission or submission.status == 'PENDING':
                # Send email
                subject = f'Homework Reminder: {homework.title}'
                message = f"""
                Dear {student.first_name},
                
                This is a reminder that your homework "{homework.title}" for {homework.class_instance.name} is due on {homework.due_date.strftime('%B %d, %Y at %I:%M %p')}.
                
                Please make sure to submit your work on time.
                
                Best regards,
                {homework.teacher.get_full_name()}
                {homework.class_instance.centre.name}
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [student.email],
                    fail_silently=True,
                )
        
        return f"Sent reminders for homework: {homework.title}"
    
    except Homework.DoesNotExist:
        return f"Homework {homework_id} not found"


@shared_task
def send_homework_graded_notification(submission_id):
    """Notify student when homework is graded"""
    try:
        submission = Submission.objects.select_related(
            'student', 'homework', 'homework__teacher'
        ).get(id=submission_id)
        
        subject = f'Homework Graded: {submission.homework.title}'
        message = f"""
        Dear {submission.student.first_name},
        
        Your homework "{submission.homework.title}" has been graded.
        
        Mark: {submission.mark}/100
        Feedback: {submission.feedback}
        
        Keep up the good work!
        
        Best regards,
        {submission.homework.teacher.get_full_name()}
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [submission.student.email],
            fail_silently=True,
        )
        
        return f"Sent grading notification to {submission.student.email}"
    
    except Submission.DoesNotExist:
        return f"Submission {submission_id} not found"


@shared_task
def send_homework_reminders():
    """
    Periodic task: Send reminders for homework due in 24 hours
    """
    tomorrow = timezone.now() + timedelta(days=1)
    start_of_tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_tomorrow = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    homework_due_tomorrow = Homework.objects.filter(
        due_date__gte=start_of_tomorrow,
        due_date__lte=end_of_tomorrow
    )
    
    count = 0
    for homework in homework_due_tomorrow:
        send_homework_reminder_email.delay(homework.id)
        count += 1
    
    return f"Queued {count} homework reminders"


@shared_task
def send_weekly_parent_digest():
    """
    Periodic task: Send weekly digest to parents about their children's progress
    """
    parents = User.objects.filter(role='PARENT', is_active=True)
    
    emails_sent = 0
    
    for parent in parents:
        links = ParentStudentLink.objects.filter(parent=parent).select_related('student')
        
        if not links.exists():
            continue
        
        # Compile digest for each linked student
        digest_content = f"Dear {parent.first_name},\n\nHere's your weekly update:\n\n"
        
        for link in links:
            student = link.student
            
            # Get recent submissions
            week_ago = timezone.now() - timedelta(days=7)
            recent_submissions = Submission.objects.filter(
                student=student,
                submitted_at__gte=week_ago
            ).select_related('homework')
            
            digest_content += f"\n{student.get_full_name()} ({link.relationship}):\n"
            digest_content += f"- Homework submitted: {recent_submissions.count()}\n"
            
            graded = recent_submissions.filter(status='GRADED', mark__isnull=False)
            if graded.exists():
                avg_mark = sum(s.mark for s in graded) / len(graded)
                digest_content += f"- Average mark: {avg_mark:.1f}/100\n"
        
        digest_content += "\n\nBest regards,\nSchool Portal Team"
        
        # Send email
        send_mail(
            'Weekly Student Progress Digest',
            digest_content,
            settings.DEFAULT_FROM_EMAIL,
            [parent.email],
            fail_silently=True,
        )
        
        emails_sent += 1
    
    return f"Sent {emails_sent} weekly digests to parents"


@shared_task
def send_sms_notification(phone_number, message):
    """
    Send SMS notification using Twilio (Phase 3)
    Requires TWILIO configuration in settings
    """
    try:
        from twilio.rest import Client
        
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_phone = settings.TWILIO_PHONE_NUMBER
        
        if not all([account_sid, auth_token, from_phone]):
            return "Twilio not configured"
        
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=message,
            from_=from_phone,
            to=phone_number
        )
        
        return f"SMS sent: {message.sid}"
    
    except ImportError:
        return "Twilio library not installed"
    except Exception as e:
        return f"Error sending SMS: {str(e)}"


@shared_task
def cleanup_old_sessions():
    """
    Periodic task: Clean up old whiteboard sessions
    Close sessions that have been active for more than 24 hours
    """
    day_ago = timezone.now() - timedelta(hours=24)
    
    old_sessions = WhiteboardSession.objects.filter(
        is_active=True,
        started_at__lte=day_ago
    )
    
    count = old_sessions.count()
    
    for session in old_sessions:
        session.end_session()
    
    return f"Closed {count} old whiteboard sessions"


@shared_task
def generate_centre_report(centre_id):
    """
    Generate comprehensive centre report (can be scheduled or on-demand)
    """
    from apps.centres.models import Centre
    from apps.classes.models import Class
    
    try:
        centre = Centre.objects.get(id=centre_id)
        
        # Gather statistics
        students = User.objects.filter(centre=centre, role='STUDENT', is_active=True).count()
        teachers = User.objects.filter(centre=centre, role='TEACHER', is_active=True).count()
        classes = Class.objects.filter(centre=centre).count()
        
        homework = Homework.objects.filter(class_instance__centre=centre)
        submissions = Submission.objects.filter(homework__in=homework, status='GRADED', mark__isnull=False)
        
        avg_mark = submissions.aggregate(models.Avg('mark'))['mark__avg'] or 0
        
        report = f"""
        Centre Report: {centre.name}
        Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Statistics:
        - Students: {students}
        - Teachers: {teachers}
        - Classes: {classes}
        - Total Homework: {homework.count()}
        - Average Mark: {avg_mark:.2f}
        """
        
        # Send report to centre manager
        managers = User.objects.filter(centre=centre, role='CENTRE_MANAGER', is_active=True)
        
        for manager in managers:
            send_mail(
                f'Centre Report: {centre.name}',
                report,
                settings.DEFAULT_FROM_EMAIL,
                [manager.email],
                fail_silently=True,
            )
        
        return f"Report generated and sent for {centre.name}"
    
    except Centre.DoesNotExist:
        return f"Centre {centre_id} not found"

