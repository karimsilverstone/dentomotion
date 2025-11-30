from rest_framework import serializers
from .models import Centre, Holiday, TermDate


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ['id', 'centre', 'name', 'date', 'is_recurring']
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
    
    class Meta:
        model = Centre
        fields = [
            'id', 'name', 'country', 'city', 'timezone',
            'holidays', 'term_dates', 'local_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_local_time(self, obj):
        return obj.get_local_time().isoformat()


class CentreCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centre
        fields = ['name', 'country', 'city', 'timezone']

