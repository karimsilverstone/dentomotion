from rest_framework import serializers
from .models import WhiteboardSession, WhiteboardSnapshot
from apps.users.serializers import UserSerializer


class WhiteboardSnapshotSerializer(serializers.ModelSerializer):
    saved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = WhiteboardSnapshot
        fields = ['id', 'session', 'snapshot_data', 'saved_at', 'saved_by', 'name']
        read_only_fields = ['id', 'saved_at']


class WhiteboardSessionSerializer(serializers.ModelSerializer):
    teacher = UserSerializer(read_only=True)
    class_name = serializers.CharField(source='class_instance.name', read_only=True)
    snapshots = WhiteboardSnapshotSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = WhiteboardSession
        fields = [
            'id', 'class_instance', 'class_name', 'teacher', 'session_name',
            'started_at', 'ended_at', 'is_active', 'snapshots', 'duration'
        ]
        read_only_fields = ['id', 'teacher', 'started_at', 'ended_at']
    
    def get_duration(self, obj):
        """Calculate session duration in minutes"""
        if obj.ended_at:
            duration = obj.ended_at - obj.started_at
            return int(duration.total_seconds() / 60)
        return None


class WhiteboardSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhiteboardSession
        fields = ['class_instance', 'session_name']

