from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'phone_number', 'role', 'status',
        'is_verified', 'created_at', 'get_role_badge'
    )
    list_filter = (
        'role', 'status', 'is_verified', 'is_active', 'is_staff',
        'is_superuser', 'created_at'
    )
    search_fields = ('username', 'email', 'phone_number', 'id_card_number')
    ordering = ('-created_at',)
    list_per_page = 25
    list_editable = ('status', 'is_verified')

    fieldsets = (
        ('Personal Information', {
            'fields': (
                'username', 'email', 'phone_number', 'role',
                'profile_photo', 'bio'
            )
        }),
        ('Account Status', {
            'fields': ('status', 'is_active', 'is_verified')
        }),
        ('KYC Information', {
            'fields': ('id_card_number', 'id_card_photo'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')

    def get_role_badge(self, obj):
        colors = {
            'ADMIN': '#f44336',
            'DALALI': '#2196f3',
            'MTEJA': '#4caf50'
        }
        color = colors.get(obj.role, '#9e9e9e')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color,
            obj.get_role_display()
        )
    get_role_badge.short_description = 'Role'

    actions = ['verify_users', 'suspend_users']

    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users verified.')
    verify_users.short_description = 'Verify selected users'

    def suspend_users(self, request, queryset):
        updated = queryset.update(status=User.Status.SUSPENDED)
        self.message_user(request, f'{updated} users suspended.')
    suspend_users.short_description = 'Suspend selected users'

admin.site.register(User, CustomUserAdmin)