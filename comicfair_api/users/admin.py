from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'real_name', 'role', 'email', 'phone', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'real_name', 'email', 'phone', 'organization')
    fieldsets = UserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('role', 'phone', 'real_name', 'organization', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('扩展信息', {'fields': ('role', 'phone', 'real_name', 'organization', 'avatar')}),
    )
