from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone', 'is_staff', 'created_at')
    list_filter = ('role', 'is_staff', 'is_superuser', 'created_at')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone', 'email')
        }),
    )