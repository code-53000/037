from django.contrib import admin
from .models import BoothZone, Booth


class BoothInline(admin.TabularInline):
    model = Booth
    extra = 0
    fields = ('booth_code', 'status', 'grid_x', 'grid_y', 'width_units', 'height_units')


@admin.register(BoothZone)
class BoothZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'exhibition', 'zone_type', 'booth_price', 'created_at')
    list_filter = ('zone_type', 'exhibition')
    search_fields = ('name', 'exhibition__name')
    inlines = [BoothInline]


@admin.register(Booth)
class BoothAdmin(admin.ModelAdmin):
    list_display = ('full_code', 'zone', 'status', 'grid_x', 'grid_y', 'created_at')
    list_filter = ('status', 'zone__zone_type', 'zone__exhibition')
    search_fields = ('booth_code', 'zone__name', 'zone__exhibition__name')
