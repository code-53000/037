from django.contrib import admin
from .models import BoothApplication


@admin.register(BoothApplication)
class BoothApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'club_name', 'applicant', 'exhibition', 'preferred_zone',
        'booth', 'status', 'fee_amount', 'paid_amount', 'created_at',
    )
    list_filter = ('status', 'exhibition', 'preferred_zone')
    search_fields = (
        'club_name', 'applicant__username', 'contact_name',
        'contact_phone', 'exhibition__name',
    )
    readonly_fields = (
        'submitted_at', 'reviewed_at', 'paid_at',
        'checked_in_at', 'created_at', 'updated_at',
    )
    date_hierarchy = 'created_at'
