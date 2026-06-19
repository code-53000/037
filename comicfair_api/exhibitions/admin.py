from django.contrib import admin
from .models import Exhibition


@admin.register(Exhibition)
class ExhibitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'venue', 'status', 'max_visitors', 'created_at')
    list_filter = ('status', 'start_date')
    search_fields = ('name', 'venue', 'address')
    date_hierarchy = 'start_date'
