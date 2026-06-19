from django.contrib import admin
from .models import CheckInGate, CheckIn


@admin.register(CheckInGate)
class CheckInGateAdmin(admin.ModelAdmin):
    list_display = ('name', 'exhibition', 'gate_type', 'location', 'is_active', 'created_at')
    list_filter = ('gate_type', 'is_active', 'exhibition')
    search_fields = ('name', 'location', 'exhibition__name')


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = (
        'checkin_type', 'status', 'person_name', 'gate', 'operator', 'checkin_time',
    )
    list_filter = ('checkin_type', 'status', 'exhibition')
    search_fields = ('code_used', 'person_name', 'operator__username')
    date_hierarchy = 'checkin_time'
    readonly_fields = ('checkin_time',)
