from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, ActivityLog, ParentStudentLink


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with role-based field exposure"""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'centre', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password',
            'password_confirm', 'role', 'centre'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'centre', 'is_active']
        
    def validate_role(self, value):
        """Validate role change"""
        # Only super admin or centre manager can change roles
        request = self.context.get('request')
        if request and request.user.role not in ['SUPER_ADMIN', 'CENTRE_MANAGER']:
            raise serializers.ValidationError("You do not have permission to change user roles.")
        return value
    
    def validate_centre(self, value):
        """Validate centre change"""
        # Only super admin can change centres
        request = self.context.get('request')
        if request and request.user.role != 'SUPER_ADMIN':
            raise serializers.ValidationError("Only Super Admin can change user centres.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class LoginSerializer(serializers.Serializer):
    """Serializer for login request"""
    
    email = serializers.EmailField(required=True, help_text="User's email address")
    password = serializers.CharField(required=True, write_only=True, help_text="User's password")


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response"""
    
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")
    user = UserSerializer(help_text="User details")


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout request"""
    
    refresh = serializers.CharField(required=True, help_text="Refresh token to blacklist")


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_email', 'action_type', 'description',
            'timestamp', 'ip_address'
        ]
        read_only_fields = ['id', 'timestamp']


class ParentStudentLinkSerializer(serializers.ModelSerializer):
    """Serializer for parent-student links"""
    
    parent = UserSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    parent_id = serializers.IntegerField(write_only=True)
    student_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ParentStudentLink
        fields = [
            'id', 'parent', 'student', 'parent_id', 'student_id',
            'relationship', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_parent_id(self, value):
        """Validate parent exists and has PARENT role"""
        try:
            user = User.objects.get(id=value)
            if user.role != 'PARENT':
                raise serializers.ValidationError("User must have role PARENT.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Parent user not found.")
    
    def validate_student_id(self, value):
        """Validate student exists and has STUDENT role"""
        try:
            user = User.objects.get(id=value)
            if user.role != 'STUDENT':
                raise serializers.ValidationError("User must have role STUDENT.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Student user not found.")
    
    def validate(self, attrs):
        """Validate parent and student are in same centre"""
        parent = User.objects.get(id=attrs['parent_id'])
        student = User.objects.get(id=attrs['student_id'])
        
        if parent.centre != student.centre:
            raise serializers.ValidationError(
                "Parent and student must be in the same centre."
            )
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Complete user profile serializer"""
    
    full_name = serializers.SerializerMethodField()
    linked_students = serializers.SerializerMethodField()
    linked_parents = serializers.SerializerMethodField()
    teaching_assignments = serializers.SerializerMethodField()
    enrolled_classes = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'centre', 'is_active', 'date_joined', 'last_login',
            'linked_students', 'linked_parents', 'teaching_assignments',
            'enrolled_classes'
        ]
        read_only_fields = ['id', 'date_joined']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_linked_students(self, obj):
        """Get linked students if user is a parent"""
        if obj.role == 'PARENT':
            links = ParentStudentLink.objects.filter(parent=obj).select_related('student')
            return [{
                'id': link.student.id,
                'name': link.student.get_full_name(),
                'email': link.student.email,
                'relationship': link.relationship
            } for link in links]
        return []
    
    def get_linked_parents(self, obj):
        """Get linked parents if user is a student"""
        if obj.role == 'STUDENT':
            links = ParentStudentLink.objects.filter(student=obj).select_related('parent')
            return [{
                'id': link.parent.id,
                'name': link.parent.get_full_name(),
                'email': link.parent.email,
                'relationship': link.relationship
            } for link in links]
        return []
    
    def get_teaching_assignments(self, obj):
        """Get teaching assignments if user is a teacher"""
        if obj.role == 'TEACHER':
            from apps.classes.models import TeacherAssignment
            assignments = TeacherAssignment.objects.filter(teacher=obj).select_related('class_instance')
            return [{
                'class_id': a.class_instance.id,
                'class_name': a.class_instance.name,
                'assigned_at': a.assigned_at
            } for a in assignments]
        return []
    
    def get_enrolled_classes(self, obj):
        """Get enrolled classes if user is a student"""
        if obj.role == 'STUDENT':
            from apps.classes.models import Enrolment
            enrolments = Enrolment.objects.filter(student=obj, is_active=True).select_related('class_instance')
            return [{
                'class_id': e.class_instance.id,
                'class_name': e.class_instance.name,
                'enrolled_at': e.enrolled_at
            } for e in enrolments]
        return []

