from rest_framework import serializers
from .models import Homework, Submission
from apps.users.serializers import UserSerializer


class SubmissionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    is_late = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'homework', 'student', 'submitted_at', 'file',
            'status', 'mark', 'feedback', 'graded_at', 'graded_by',
            'is_late', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'graded_at', 'graded_by']
    
    def get_is_late(self, obj):
        return obj.is_late()


class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['file']  # Only file field - homework comes from URL
        
    def validate_file(self, value):
        """Validate file upload"""
        if not value:
            raise serializers.ValidationError("File is required for submission.")
        
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 10MB.")
        
        return value


class SubmissionGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['mark', 'feedback']
    
    def validate_mark(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Mark must be between 0 and 100.")
        return value


class HomeworkSerializer(serializers.ModelSerializer):
    teacher = UserSerializer(read_only=True)
    is_overdue = serializers.SerializerMethodField()
    submission_stats = serializers.SerializerMethodField()
    my_submission = serializers.SerializerMethodField()
    
    class Meta:
        model = Homework
        fields = [
            'id', 'class_instance', 'teacher', 'title', 'description',
            'file', 'assigned_date', 'due_date', 'is_overdue',
            'submission_stats', 'my_submission', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'teacher', 'created_at', 'updated_at']
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()
    
    def get_submission_stats(self, obj):
        return obj.get_submission_stats()
    
    def get_my_submission(self, obj):
        request = self.context.get('request')
        if request and request.user.role == 'STUDENT':
            try:
                submission = Submission.objects.get(homework=obj, student=request.user)
                return SubmissionSerializer(submission).data
            except Submission.DoesNotExist:
                return None
        return None


class HomeworkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Homework
        fields = ['class_instance', 'title', 'description', 'file', 'due_date']
    
    def validate_due_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value


class HomeworkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Homework
        fields = ['title', 'description', 'file', 'due_date']

