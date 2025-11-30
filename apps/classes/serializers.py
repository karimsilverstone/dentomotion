from rest_framework import serializers
from .models import Class, TeacherAssignment, Enrolment
from apps.users.serializers import UserSerializer


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher = UserSerializer(read_only=True)
    teacher_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TeacherAssignment
        fields = ['id', 'teacher', 'teacher_id', 'class_instance', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']
    
    def validate_teacher_id(self, value):
        from apps.users.models import User
        try:
            teacher = User.objects.get(id=value)
            if teacher.role != 'TEACHER':
                raise serializers.ValidationError("User must be a teacher.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Teacher not found.")


class EnrolmentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    student_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Enrolment
        fields = ['id', 'student', 'student_id', 'class_instance', 'enrolled_at', 'is_active']
        read_only_fields = ['id', 'enrolled_at']
    
    def validate_student_id(self, value):
        from apps.users.models import User
        try:
            student = User.objects.get(id=value)
            if student.role != 'STUDENT':
                raise serializers.ValidationError("User must be a student.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Student not found.")
    
    def validate(self, attrs):
        from apps.users.models import User
        
        student = User.objects.get(id=attrs['student_id'])
        class_instance = attrs.get('class_instance')
        
        if student.centre != class_instance.centre:
            raise serializers.ValidationError(
                "Students can only enrol in classes within their own centre."
            )
        
        return attrs


class ClassSerializer(serializers.ModelSerializer):
    teachers = TeacherAssignmentSerializer(source='teacher_assignments', many=True, read_only=True)
    students = EnrolmentSerializer(source='enrolments', many=True, read_only=True)
    teacher_count = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'centre', 'name', 'level_or_age_group',
            'teachers', 'students', 'teacher_count', 'student_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_teacher_count(self, obj):
        return obj.teacher_assignments.count()
    
    def get_student_count(self, obj):
        return obj.enrolments.filter(is_active=True).count()


class ClassCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['centre', 'name', 'level_or_age_group']

