"""
Dashboard views for different user roles
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from apps.homework.models import Homework, Submission
from apps.classes.models import Class, Enrolment
from apps.calendar.models import Event
from apps.whiteboard.models import WhiteboardSession


class TeacherDashboardView(APIView):
    """
    Dashboard for teachers
    Shows: Today's classes, homework to mark, quick whiteboard start
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'TEACHER':
            return Response({'error': 'This endpoint is for teachers only.'}, status=403)
        
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Get classes assigned to this teacher
        my_classes = Class.objects.filter(
            teacher_assignments__teacher=request.user
        ).select_related('centre')
        
        # Get homework pending marking
        pending_marking = Submission.objects.filter(
            homework__teacher=request.user,
            status='SUBMITTED'
        ).select_related('homework', 'student').order_by('submitted_at')
        
        # Get today's events
        today_events = Event.objects.filter(
            Q(centre=request.user.centre, event_type='CENTRE_EVENT') |
            Q(class_instance__teacher_assignments__teacher=request.user, event_type='CLASS_EVENT'),
            event_date__date=today
        ).distinct().select_related('class_instance')
        
        # Get active whiteboard sessions
        active_sessions = WhiteboardSession.objects.filter(
            teacher=request.user,
            is_active=True
        ).select_related('class_instance')
        
        # Get homework due soon
        homework_due_soon = Homework.objects.filter(
            teacher=request.user,
            due_date__lte=timezone.now() + timedelta(days=7),
            due_date__gte=timezone.now()
        ).select_related('class_instance').order_by('due_date')
        
        return Response({
            'overview': {
                'total_classes': my_classes.count(),
                'pending_marking': pending_marking.count(),
                'today_events': today_events.count(),
                'active_sessions': active_sessions.count(),
            },
            'my_classes': [{
                'id': cls.id,
                'name': cls.name,
                'level': cls.level_or_age_group,
                'student_count': cls.enrolments.filter(is_active=True).count()
            } for cls in my_classes],
            'pending_marking': [{
                'id': sub.id,
                'homework_title': sub.homework.title,
                'student': sub.student.get_full_name(),
                'submitted_at': sub.submitted_at,
                'days_waiting': (timezone.now() - sub.submitted_at).days
            } for sub in pending_marking[:10]],
            'today_events': [{
                'id': event.id,
                'title': event.title,
                'time': event.event_date,
                'type': event.event_type,
                'class': event.class_instance.name if event.class_instance else None
            } for event in today_events],
            'active_sessions': [{
                'id': session.id,
                'name': session.session_name,
                'class': session.class_instance.name,
                'started_at': session.started_at
            } for session in active_sessions],
            'homework_due_soon': [{
                'id': hw.id,
                'title': hw.title,
                'class': hw.class_instance.name,
                'due_date': hw.due_date,
                'submission_stats': hw.get_submission_stats()
            } for hw in homework_due_soon[:5]]
        })


class StudentDashboardView(APIView):
    """
    Dashboard for students
    Shows: Next classes, homework due, events
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'STUDENT':
            return Response({'error': 'This endpoint is for students only.'}, status=403)
        
        # Get enrolled classes
        my_enrolments = Enrolment.objects.filter(
            student=request.user,
            is_active=True
        ).select_related('class_instance')
        
        my_classes = [enrol.class_instance for enrol in my_enrolments]
        
        # Get homework due soon
        homework_due = Homework.objects.filter(
            class_instance__in=my_classes,
            due_date__gte=timezone.now()
        ).select_related('class_instance', 'teacher').order_by('due_date')
        
        # Get my submissions for this homework
        my_submissions = {}
        for hw in homework_due:
            try:
                submission = Submission.objects.get(homework=hw, student=request.user)
                my_submissions[hw.id] = {
                    'status': submission.status,
                    'submitted_at': submission.submitted_at,
                    'mark': submission.mark,
                    'feedback': submission.feedback
                }
            except Submission.DoesNotExist:
                my_submissions[hw.id] = {'status': 'NOT_SUBMITTED'}
        
        # Get upcoming events
        upcoming_events = Event.objects.filter(
            Q(centre=request.user.centre, event_type='CENTRE_EVENT') |
            Q(class_instance__in=my_classes, event_type='CLASS_EVENT'),
            event_date__gte=timezone.now()
        ).distinct().select_related('class_instance').order_by('event_date')[:10]
        
        # Get active whiteboard sessions I can join
        active_sessions = WhiteboardSession.objects.filter(
            class_instance__in=my_classes,
            is_active=True
        ).select_related('class_instance', 'teacher')
        
        return Response({
            'overview': {
                'enrolled_classes': len(my_classes),
                'homework_pending': sum(1 for hw_id, sub in my_submissions.items() if sub['status'] == 'NOT_SUBMITTED'),
                'upcoming_events': upcoming_events.count(),
                'active_sessions': active_sessions.count()
            },
            'my_classes': [{
                'id': cls.id,
                'name': cls.name,
                'level': cls.level_or_age_group
            } for cls in my_classes],
            'homework_due': [{
                'id': hw.id,
                'title': hw.title,
                'class': hw.class_instance.name,
                'teacher': hw.teacher.get_full_name(),
                'due_date': hw.due_date,
                'is_overdue': hw.is_overdue(),
                'my_submission': my_submissions.get(hw.id, {'status': 'NOT_SUBMITTED'})
            } for hw in homework_due[:10]],
            'upcoming_events': [{
                'id': event.id,
                'title': event.title,
                'date': event.event_date,
                'type': event.event_type,
                'class': event.class_instance.name if event.class_instance else None
            } for event in upcoming_events],
            'active_sessions': [{
                'id': session.id,
                'name': session.session_name,
                'class': session.class_instance.name,
                'teacher': session.teacher.get_full_name(),
                'join_url': f'/api/whiteboard/sessions/{session.id}/join/'
            } for session in active_sessions]
        })


class ManagerDashboardView(APIView):
    """
    Dashboard for centre managers
    Shows: Student/teacher count, centre events, overdue marking alerts
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'CENTRE_MANAGER':
            return Response({'error': 'This endpoint is for centre managers only.'}, status=403)
        
        centre = request.user.centre
        if not centre:
            return Response({'error': 'No centre assigned to user.'}, status=400)
        
        # Get counts
        from apps.users.models import User
        students = User.objects.filter(centre=centre, role='STUDENT', is_active=True)
        teachers = User.objects.filter(centre=centre, role='TEACHER', is_active=True)
        classes = Class.objects.filter(centre=centre)
        
        # Get overdue marking (submissions older than 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        overdue_marking = Submission.objects.filter(
            homework__class_instance__centre=centre,
            status='SUBMITTED',
            submitted_at__lte=seven_days_ago
        ).select_related('homework', 'student', 'homework__teacher')
        
        # Get upcoming centre events
        upcoming_events = Event.objects.filter(
            centre=centre,
            event_date__gte=timezone.now()
        ).order_by('event_date')[:10]
        
        # Get recent homework statistics
        recent_homework = Homework.objects.filter(
            class_instance__centre=centre,
            assigned_date__gte=timezone.now() - timedelta(days=30)
        )
        
        # Get active whiteboard sessions
        active_sessions = WhiteboardSession.objects.filter(
            class_instance__centre=centre,
            is_active=True
        ).select_related('class_instance', 'teacher')
        
        return Response({
            'overview': {
                'student_count': students.count(),
                'teacher_count': teachers.count(),
                'class_count': classes.count(),
                'overdue_marking_count': overdue_marking.count(),
                'upcoming_events': upcoming_events.count(),
                'active_sessions': active_sessions.count()
            },
            'centre_info': {
                'name': centre.name,
                'city': centre.city,
                'country': centre.country,
                'timezone': centre.timezone
            },
            'overdue_marking_alerts': [{
                'homework': marking.homework.title,
                'class': marking.homework.class_instance.name,
                'student': marking.student.get_full_name(),
                'teacher': marking.homework.teacher.get_full_name(),
                'submitted_at': marking.submitted_at,
                'days_waiting': (timezone.now() - marking.submitted_at).days
            } for marking in overdue_marking[:10]],
            'upcoming_events': [{
                'id': event.id,
                'title': event.title,
                'date': event.event_date,
                'type': event.event_type
            } for event in upcoming_events],
            'recent_homework_stats': {
                'total_assigned': recent_homework.count(),
                'average_completion_rate': self._calculate_completion_rate(recent_homework)
            },
            'active_sessions': [{
                'id': session.id,
                'name': session.session_name,
                'class': session.class_instance.name,
                'teacher': session.teacher.get_full_name(),
                'started_at': session.started_at
            } for session in active_sessions]
        })
    
    def _calculate_completion_rate(self, homework_queryset):
        """Calculate average homework completion rate"""
        if not homework_queryset.exists():
            return 0
        
        total_students = 0
        total_submitted = 0
        
        for hw in homework_queryset:
            stats = hw.get_submission_stats()
            total_students += stats['total_students']
            total_submitted += stats['submitted']
        
        if total_students == 0:
            return 0
        
        return round((total_submitted / total_students) * 100, 2)


class ParentDashboardView(APIView):
    """
    Dashboard for parents
    Shows: Linked students' homework, marks, events
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'PARENT':
            return Response({'error': 'This endpoint is for parents only.'}, status=403)
        
        from apps.users.models import ParentStudentLink
        
        # Get linked students
        links = ParentStudentLink.objects.filter(parent=request.user).select_related('student')
        
        if not links.exists():
            return Response({
                'message': 'No students linked to this parent account.',
                'students': []
            })
        
        students_data = []
        
        for link in links:
            student = link.student
            
            # Get student's classes
            enrolments = Enrolment.objects.filter(
                student=student,
                is_active=True
            ).select_related('class_instance')
            
            student_classes = [enrol.class_instance for enrol in enrolments]
            
            # Get homework
            homework = Homework.objects.filter(
                class_instance__in=student_classes
            ).select_related('class_instance', 'teacher').order_by('-assigned_date')[:10]
            
            # Get submissions
            submissions = Submission.objects.filter(
                student=student,
                homework__in=homework
            ).select_related('homework')
            
            submissions_dict = {sub.homework.id: sub for sub in submissions}
            
            # Get upcoming events
            upcoming_events = Event.objects.filter(
                Q(centre=student.centre, event_type='CENTRE_EVENT') |
                Q(class_instance__in=student_classes, event_type='CLASS_EVENT'),
                event_date__gte=timezone.now()
            ).distinct().order_by('event_date')[:5]
            
            students_data.append({
                'student': {
                    'id': student.id,
                    'name': student.get_full_name(),
                    'relationship': link.relationship
                },
                'classes': [{
                    'id': cls.id,
                    'name': cls.name,
                    'level': cls.level_or_age_group
                } for cls in student_classes],
                'recent_homework': [{
                    'id': hw.id,
                    'title': hw.title,
                    'class': hw.class_instance.name,
                    'due_date': hw.due_date,
                    'submission': {
                        'status': submissions_dict[hw.id].status if hw.id in submissions_dict else 'NOT_SUBMITTED',
                        'mark': submissions_dict[hw.id].mark if hw.id in submissions_dict else None,
                        'feedback': submissions_dict[hw.id].feedback if hw.id in submissions_dict else None,
                        'submitted_at': submissions_dict[hw.id].submitted_at if hw.id in submissions_dict else None
                    }
                } for hw in homework],
                'upcoming_events': [{
                    'id': event.id,
                    'title': event.title,
                    'date': event.event_date,
                    'type': event.event_type
                } for event in upcoming_events]
            })
        
        return Response({
            'students': students_data
        })

