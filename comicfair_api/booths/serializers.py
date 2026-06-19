from rest_framework import serializers
from .models import BoothZone, Booth, ZoneType, BoothStatus


class BoothSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    full_code = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booth
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'status_display', 'full_code', 'is_available')


class BoothZoneSerializer(serializers.ModelSerializer):
    zone_type_display = serializers.CharField(source='get_zone_type_display', read_only=True)
    booths = BoothSerializer(many=True, read_only=True)
    booth_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = BoothZone
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'zone_type_display', 'booths', 'booth_count')


class BoothZoneMapSerializer(serializers.Serializer):
    zone_id = serializers.IntegerField()
    zone_name = serializers.CharField()
    zone_type = serializers.CharField()
    color = serializers.CharField()
    position_x = serializers.IntegerField()
    position_y = serializers.IntegerField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    booth_price = serializers.CharField()
    booths = BoothSerializer(many=True)
    stats = serializers.DictField()
