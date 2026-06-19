from django.contrib import admin
from .models import TicketTier, Ticket


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    fields = ('ticket_no', 'user', 'ticket_type', 'status', 'price', 'created_at')
    readonly_fields = ('ticket_no', 'ticket_code', 'created_at')


@admin.register(TicketTier)
class TicketTierAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'exhibition', 'ticket_type', 'price',
        'quantity', 'sold_count', 'remaining', 'on_sale', 'created_at',
    )
    list_filter = ('ticket_type', 'on_sale', 'exhibition')
    search_fields = ('name', 'exhibition__name')
    inlines = [TicketInline]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_no', 'user', 'exhibition', 'tier', 'ticket_type',
        'status', 'price', 'paid_at', 'used_at', 'created_at',
    )
    list_filter = ('ticket_type', 'status', 'exhibition')
    search_fields = (
        'ticket_no', 'ticket_code', 'user__username',
        'holder_name', 'holder_phone',
    )
    readonly_fields = ('ticket_no', 'ticket_code', 'created_at')
    date_hierarchy = 'created_at'
