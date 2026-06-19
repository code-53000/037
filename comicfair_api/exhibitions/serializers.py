from rest_framework import serializers
from .models import Exhibition


class ExhibitionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Exhibition
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'duration_days', 'is_active', 'status_display')
