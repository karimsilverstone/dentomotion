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
    teacher_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="Optional list of teacher IDs to assign to this class"
    )
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="Optional list of student IDs to enroll in this class"
    )
    
    class Meta:
        model = Class
        fields = ['centre', 'name', 'level_or_age_group', 'teacher_ids', 'student_ids']
    
    def validate_teacher_ids(self, value):
        """Validate that all teacher IDs are valid teachers"""
        if not value:
            return value
            
        from apps.users.models import User
        
        for teacher_id in value:
            try:
                teacher = User.objects.get(id=teacher_id)
                if teacher.role != 'TEACHER':
                    raise serializers.ValidationError(
                        f"User with ID {teacher_id} is not a teacher."
                    )
                # Check if teacher already has 3 classes
                if teacher.teaching_assignments.count() >= 3:
                    raise serializers.ValidationError(
                        f"Teacher {teacher.get_full_name()} already has 3 classes assigned."
                    )
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    f"Teacher with ID {teacher_id} not found."
                )
        
        return value
    
    def validate_student_ids(self, value):
        """Validate that all student IDs are valid students"""
        if not value:
            return value
            
        from apps.users.models import User
        
        for student_id in value:
            try:
                student = User.objects.get(id=student_id)
                if student.role != 'STUDENT':
                    raise serializers.ValidationError(
                        f"User with ID {student_id} is not a student."
                    )
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    f"Student with ID {student_id} not found."
                )
        
        return value
    
    def validate(self, attrs):
        """Validate that students belong to the same centre as the class"""
        student_ids = attrs.get('student_ids', [])
        centre = attrs.get('centre')
        
        if student_ids and centre:
            from apps.users.models import User
            for student_id in student_ids:
                student = User.objects.get(id=student_id)
                if student.centre != centre:
                    raise serializers.ValidationError(
                        f"Student {student.get_full_name()} is not in the same centre as this class."
                    )
        
        return attrs
    
    def create(self, validated_data):
        """Create class and assign teachers/students if provided"""
        teacher_ids = validated_data.pop('teacher_ids', [])
        student_ids = validated_data.pop('student_ids', [])
        
        # Create the class
        class_instance = Class.objects.create(**validated_data)
        
        # Assign teachers if provided
        if teacher_ids:
            from apps.users.models import User
            for teacher_id in teacher_ids:
                teacher = User.objects.get(id=teacher_id)
                TeacherAssignment.objects.create(
                    teacher=teacher,
                    class_instance=class_instance
                )
        
        # Enroll students if provided
        if student_ids:
            from apps.users.models import User
            for student_id in student_ids:
                student = User.objects.get(id=student_id)
                Enrolment.objects.create(
                    student=student,
                    class_instance=class_instance
                )
        
        return class_instance

