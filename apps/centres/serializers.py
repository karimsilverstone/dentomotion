from rest_framework import serializers
from .models import Centre, Holiday, TermDate, CentreManagerAssignment


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ['id', 'centre', 'name', 'description', 'date', 'is_recurring']
        read_only_fields = ['id']


class TermDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermDate
        fields = ['id', 'centre', 'term_name', 'start_date', 'end_date']
        read_only_fields = ['id']
    
    def validate(self, attrs):
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['start_date'] >= attrs['end_date']:
                raise serializers.ValidationError("End date must be after start date.")
        return attrs


class CentreSerializer(serializers.ModelSerializer):
    holidays = HolidaySerializer(many=True, read_only=True)
    term_dates = TermDateSerializer(many=True, read_only=True)
    local_time = serializers.SerializerMethodField()
    manager = serializers.SerializerMethodField()
    
    class Meta:
        model = Centre
        fields = [
            'id', 'name', 'country', 'city', 'timezone',
            'manager', 'holidays', 'term_dates', 'local_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_local_time(self, obj):
        return obj.get_local_time().isoformat()
    
    def get_manager(self, obj):
        """Get all centre managers (can be multiple)"""
        from apps.users.models import User
        
        try:
            # Try to get managers through assignments (new way)
            assignments = CentreManagerAssignment.objects.filter(centre=obj).select_related('manager')
            
            if assignments.exists():
                return [{
                    'id': assignment.manager.id,
                    'email': assignment.manager.email,
                    'first_name': assignment.manager.first_name,
                    'last_name': assignment.manager.last_name,
                    'is_primary': assignment.is_primary
                } for assignment in assignments]
        except Exception as e:
            # If CentreManagerAssignment table doesn't exist yet (before migration)
            # Fall back to old method
            pass
        
        # Fallback: check old way (for backward compatibility)
        try:
            managers = User.objects.filter(centre=obj, role='CENTRE_MANAGER')
            if managers.exists():
                return [{
                    'id': manager.id,
                    'email': manager.email,
                    'first_name': manager.first_name,
                    'last_name': manager.last_name,
                    'is_primary': True
                } for manager in managers]
        except Exception:
            pass
        
        return []


class CentreUpdateSerializer(serializers.ModelSerializer):
    centre_manager_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of the user to assign as new Centre Manager (optional)"
    )
    
    class Meta:
        model = Centre
        fields = ['name', 'country', 'city', 'timezone', 'centre_manager_id']
    
    def validate_centre_manager_id(self, value):
        """Validate that the user exists and can be a centre manager"""
        if value is None:
            return value
            
        from apps.users.models import User
        
        try:
            user = User.objects.get(id=value)
            
            # Check if user is already managing a different centre
            if user.role == 'CENTRE_MANAGER' and user.centre is not None:
                # Allow if they're managing THIS centre (no change)
                if user.centre.id != self.instance.id:
                    raise serializers.ValidationError(
                        f"User {user.get_full_name()} is already managing another centre."
                    )
            
            # Check if user has a role that prevents being a manager
            if user.role == 'SUPER_ADMIN':
                raise serializers.ValidationError(
                    "Super Admin cannot be assigned as a Centre Manager."
                )
            
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
    
    def update(self, instance, validated_data):
        """Update centre and optionally change manager"""
        from apps.users.models import User
        
        centre_manager_id = validated_data.pop('centre_manager_id', None)
        
        # Update centre basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Change manager if new manager_id provided
        if centre_manager_id is not None:
            # Get the old manager (if exists)
            old_manager = User.objects.filter(
                centre=instance,
                role='CENTRE_MANAGER'
            ).first()
            
            # Try new way with assignments
            try:
                # Remove old manager assignment (if changing)
                if old_manager and old_manager.id != centre_manager_id:
                    # Remove assignment for this centre
                    CentreManagerAssignment.objects.filter(
                        manager=old_manager,
                        centre=instance
                    ).delete()
                    
                    # If old manager has no other centres, demote them
                    if not CentreManagerAssignment.objects.filter(manager=old_manager).exists():
                        old_manager.role = 'TEACHER'
                        old_manager.centre = None
                        old_manager.save(update_fields=['role', 'centre'])
                
                # Assign new manager
                new_manager = User.objects.get(id=centre_manager_id)
                
                # Update role if not already a manager
                if new_manager.role != 'CENTRE_MANAGER':
                    new_manager.role = 'CENTRE_MANAGER'
                    new_manager.save(update_fields=['role'])
                
                # Create or get assignment
                CentreManagerAssignment.objects.get_or_create(
                    manager=new_manager,
                    centre=instance
                )
                
                # Set primary centre if user doesn't have one
                if new_manager.centre is None:
                    new_manager.centre = instance
                    new_manager.save(update_fields=['centre'])
            except Exception:
                # Fallback to old way if table doesn't exist
                new_manager = User.objects.get(id=centre_manager_id)
                new_manager.role = 'CENTRE_MANAGER'
                new_manager.centre = instance
                new_manager.save(update_fields=['role', 'centre'])
        
        return instance


class CentreCreateSerializer(serializers.ModelSerializer):
    centre_manager_id = serializers.IntegerField(
        write_only=True,
        required=True,
        help_text="ID of the user to assign as Centre Manager"
    )
    
    class Meta:
        model = Centre
        fields = ['name', 'country', 'city', 'timezone', 'centre_manager_id']
    
    def validate_centre_manager_id(self, value):
        """Validate that the user exists and can be a centre manager"""
        from apps.users.models import User
        
        try:
            user = User.objects.get(id=value)
            
            # Check if user has a role that prevents being a manager
            if user.role == 'SUPER_ADMIN':
                raise serializers.ValidationError(
                    "Super Admin cannot be assigned as a Centre Manager."
                )
            
            # Note: Centre managers can now manage multiple centres
            # So we don't check if they're already managing another centre
            
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
    
    def create(self, validated_data):
        """Create centre and assign manager"""
        from apps.users.models import User
        
        centre_manager_id = validated_data.pop('centre_manager_id')
        
        # Create the centre
        centre = Centre.objects.create(**validated_data)
        
        # Assign the user as centre manager
        user = User.objects.get(id=centre_manager_id)
        
        # Update user role if not already a manager
        if user.role != 'CENTRE_MANAGER':
            user.role = 'CENTRE_MANAGER'
            user.save(update_fields=['role'])
        
        # Try to create manager assignment (new way)
        try:
            CentreManagerAssignment.objects.create(
                manager=user,
                centre=centre,
                is_primary=(user.centre is None)
            )
        except Exception:
            # If table doesn't exist yet (before migration), skip
            pass
        
        # Set primary centre if user doesn't have one
        if user.centre is None:
            user.centre = centre
            user.save(update_fields=['centre'])
        
        return centre

