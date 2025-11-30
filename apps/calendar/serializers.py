from rest_framework import serializers
from .models import Event
from apps.users.serializers import UserSerializer


class EventSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    centre_name = serializers.CharField(source='centre.name', read_only=True)
    class_name = serializers.CharField(source='class_instance.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'centre', 'centre_name', 'class_instance', 'class_name',
            'title', 'description', 'event_date', 'event_type',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        event_type = attrs.get('event_type')
        class_instance = attrs.get('class_instance')
        
        if event_type == 'CLASS_EVENT' and not class_instance:
            raise serializers.ValidationError("Class events must have a class specified.")
        
        if event_type == 'CENTRE_EVENT' and class_instance:
            raise serializers.ValidationError("Centre events should not have a class specified.")
        
        return attrs


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['centre', 'class_instance', 'title', 'description', 'event_date', 'event_type']
    
    def validate(self, attrs):
        event_type = attrs.get('event_type')
        class_instance = attrs.get('class_instance')
        
        if event_type == 'CLASS_EVENT' and not class_instance:
            raise serializers.ValidationError("Class events must have a class specified.")
        
        if event_type == 'CENTRE_EVENT' and class_instance:
            raise serializers.ValidationError("Centre events should not have a class specified.")
        
        return attrs

