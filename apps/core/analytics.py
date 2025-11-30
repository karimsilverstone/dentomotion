"""
Analytics views for Centre Managers and Super Admins
Provides insights into homework trends, student performance, and centre overview
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate
from apps.homework.models import Homework, Submission
from apps.classes.models import Class, Enrolment
from apps.users.models import User
from apps.whiteboard.models import WhiteboardSession


class HomeworkTrendsView(APIView):
    """
    Homework submission trends over time
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['CENTRE_MANAGER', 'SUPER_ADMIN']:
            return Response({'error': 'Access denied.'}, status=403)
        
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Filter by centre for managers
        if request.user.role == 'CENTRE_MANAGER':
            homework_qs = Homework.objects.filter(
                class_instance__centre=request.user.centre,
                assigned_date__gte=start_date
            )
        else:
            homework_qs = Homework.objects.filter(assigned_date__gte=start_date)
        
        # Homework assigned over time
        homework_by_date = homework_qs.annotate(
            date=TruncDate('assigned_date')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Submission statistics
        total_homework = homework_qs.count()
        total_submissions = Submission.objects.filter(homework__in=homework_qs)
        
        submission_stats = {
            'total_homework': total_homework,
            'total_submissions': total_submissions.count(),
            'submitted': total_submissions.filter(status__in=['SUBMITTED', 'GRADED']).count(),
            'graded': total_submissions.filter(status='GRADED').count(),
            'pending': total_submissions.filter(status='PENDING').count()
        }
        
        # Submission rate by class
        if request.user.role == 'CENTRE_MANAGER':
            classes = Class.objects.filter(centre=request.user.centre)
        else:
            classes = Class.objects.all()
        
        class_stats = []
        for cls in classes:
            hw_in_class = homework_qs.filter(class_instance=cls)
            if hw_in_class.exists():
                student_count = cls.enrolments.filter(is_active=True).count()
                expected_submissions = hw_in_class.count() * student_count
                actual_submissions = Submission.objects.filter(
                    homework__in=hw_in_class,
                    status__in=['SUBMITTED', 'GRADED']
                ).count()
                
                completion_rate = (actual_submissions / expected_submissions * 100) if expected_submissions > 0 else 0
                
                class_stats.append({
                    'class_name': cls.name,
                    'homework_count': hw_in_class.count(),
                    'student_count': student_count,
                    'completion_rate': round(completion_rate, 2)
                })
        
        return Response({
            'period': f'Last {days} days',
            'homework_by_date': list(homework_by_date),
            'submission_stats': submission_stats,
            'class_stats': class_stats
        })


class StudentPerformanceView(APIView):
    """
    Student performance analytics
    Shows average marks, completion rates, etc.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['CENTRE_MANAGER', 'SUPER_ADMIN']:
            return Response({'error': 'Access denied.'}, status=403)
        
        # Filter by centre for managers
        if request.user.role == 'CENTRE_MANAGER':
            students = User.objects.filter(
                role='STUDENT',
                centre=request.user.centre,
                is_active=True
            )
        else:
            students = User.objects.filter(role='STUDENT', is_active=True)
        
        student_stats = []
        
        for student in students[:50]:  # Limit to 50 for performance
            submissions = Submission.objects.filter(student=student)
            graded_submissions = submissions.filter(status='GRADED', mark__isnull=False)
            
            total_homework = Homework.objects.filter(
                class_instance__enrolments__student=student,
                class_instance__enrolments__is_active=True
            ).count()
            
            submitted_count = submissions.filter(status__in=['SUBMITTED', 'GRADED']).count()
            completion_rate = (submitted_count / total_homework * 100) if total_homework > 0 else 0
            
            avg_mark = graded_submissions.aggregate(Avg('mark'))['mark__avg'] or 0
            
            student_stats.append({
                'student_id': student.id,
                'student_name': student.get_full_name(),
                'total_homework': total_homework,
                'submitted': submitted_count,
                'completion_rate': round(completion_rate, 2),
                'average_mark': round(avg_mark, 2) if avg_mark else None,
                'graded_count': graded_submissions.count()
            })
        
        # Sort by completion rate descending
        student_stats.sort(key=lambda x: x['completion_rate'], reverse=True)
        
        # Overall statistics
        all_submissions = Submission.objects.filter(student__in=students, status='GRADED', mark__isnull=False)
        overall_avg = all_submissions.aggregate(Avg('mark'))['mark__avg'] or 0
        
        return Response({
            'overall_average_mark': round(overall_avg, 2),
            'total_students': students.count(),
            'student_stats': student_stats
        })


class CentreOverviewView(APIView):
    """
    Centre overview analytics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['CENTRE_MANAGER', 'SUPER_ADMIN']:
            return Response({'error': 'Access denied.'}, status=403)
        
        from apps.centres.models import Centre
        
        # Get centres to analyze
        if request.user.role == 'CENTRE_MANAGER':
            centres = [request.user.centre]
        else:
            centres = Centre.objects.all()
        
        centre_data = []
        
        for centre in centres:
            # Get counts
            students = User.objects.filter(centre=centre, role='STUDENT', is_active=True).count()
            teachers = User.objects.filter(centre=centre, role='TEACHER', is_active=True).count()
            classes = Class.objects.filter(centre=centre).count()
            
            # Homework statistics
            homework = Homework.objects.filter(class_instance__centre=centre)
            total_homework = homework.count()
            
            recent_homework = homework.filter(
                assigned_date__gte=timezone.now() - timedelta(days=30)
            )
            
            # Calculate completion rate
            total_expected = 0
            total_submitted = 0
            
            for hw in recent_homework:
                student_count = hw.class_instance.enrolments.filter(is_active=True).count()
                total_expected += student_count
                total_submitted += hw.submissions.filter(status__in=['SUBMITTED', 'GRADED']).count()
            
            completion_rate = (total_submitted / total_expected * 100) if total_expected > 0 else 0
            
            # Whiteboard usage
            whiteboard_sessions = WhiteboardSession.objects.filter(
                class_instance__centre=centre,
                started_at__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            centre_data.append({
                'centre_id': centre.id,
                'centre_name': centre.name,
                'location': f"{centre.city}, {centre.country}",
                'students': students,
                'teachers': teachers,
                'classes': classes,
                'total_homework': total_homework,
                'recent_homework': recent_homework.count(),
                'completion_rate': round(completion_rate, 2),
                'whiteboard_sessions_30d': whiteboard_sessions
            })
        
        return Response({
            'centres': centre_data,
            'generated_at': timezone.now()
        })


class TeacherPerformanceView(APIView):
    """
    Teacher performance metrics
    Average grading time, feedback quality, etc.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['CENTRE_MANAGER', 'SUPER_ADMIN']:
            return Response({'error': 'Access denied.'}, status=403)
        
        # Filter by centre for managers
        if request.user.role == 'CENTRE_MANAGER':
            teachers = User.objects.filter(
                role='TEACHER',
                centre=request.user.centre,
                is_active=True
            )
        else:
            teachers = User.objects.filter(role='TEACHER', is_active=True)
        
        teacher_stats = []
        
        for teacher in teachers:
            homework_assigned = Homework.objects.filter(teacher=teacher)
            
            # Submissions graded by this teacher
            graded = Submission.objects.filter(
                homework__teacher=teacher,
                status='GRADED',
                graded_at__isnull=False
            )
            
            # Calculate average grading time
            grading_times = []
            for sub in graded:
                if sub.submitted_at and sub.graded_at:
                    time_diff = sub.graded_at - sub.submitted_at
                    grading_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
            
            avg_grading_time = sum(grading_times) / len(grading_times) if grading_times else 0
            
            # Feedback quality (percentage with feedback)
            with_feedback = graded.exclude(feedback='').count()
            feedback_rate = (with_feedback / graded.count() * 100) if graded.count() > 0 else 0
            
            # Whiteboard usage
            whiteboard_sessions = WhiteboardSession.objects.filter(
                teacher=teacher,
                started_at__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            teacher_stats.append({
                'teacher_id': teacher.id,
                'teacher_name': teacher.get_full_name(),
                'homework_assigned': homework_assigned.count(),
                'submissions_graded': graded.count(),
                'avg_grading_time_hours': round(avg_grading_time, 2),
                'feedback_rate': round(feedback_rate, 2),
                'whiteboard_sessions_30d': whiteboard_sessions
            })
        
        return Response({
            'teachers': teacher_stats,
            'total_teachers': teachers.count()
        })

