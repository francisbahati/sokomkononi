from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import User

class CustomUserAdmin(UserAdmin):
    """Custom admin for User model with all fields"""
    
    # Fields to display in the list view
    list_display = (
        'username', 
        'email', 
        'phone_number', 
        'role', 
        'is_verified',
        'is_active',
        'get_role_badge',
        'created_at'
    )
    
    # Fields to filter by
    list_filter = (
        'role', 
        'is_verified', 
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at'
    )
    
    # Fields to search
    search_fields = (
        'username', 
        'email', 
        'phone_number',
        'id_card_number'
    )
    
    # Fields to order by
    ordering = ('-created_at',)
    
    # Number of items per page
    list_per_page = 25
    
    # Fields that can be edited directly from list view
    list_editable = ('is_verified', 'is_active')
    
    # Fieldsets for the detail/edit page
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'username', 
                'email', 
                'phone_number', 
                'role',
                'profile_photo',
                'bio'
            )
        }),
        ('KYC Information', {
            'fields': (
                'is_verified',
                'id_card_number',
                'id_card_photo'
            ),
            'classes': ('collapse',)
        }),
        ('Account Status', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser'
            )
        }),
        ('Important Dates', {
            'fields': (
                'last_login',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': (
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
    )
    
    # Fields that are read-only
    readonly_fields = (
        'created_at', 
        'updated_at',
        'last_login'
    )
    
    # Add custom method to display role as a badge
    def get_role_badge(self, obj):
        """Display role with colored badge"""
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
    
    # Add custom action to verify multiple users at once
    actions = ['verify_users', 'suspend_users']
    
    def verify_users(self, request, queryset):
        """Admin action to verify selected users"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users were successfully verified.')
    verify_users.short_description = 'Verify selected users'
    
    def suspend_users(self, request, queryset):
        """Admin action to suspend selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were suspended.')
    suspend_users.short_description = 'Suspend selected users'

# Register the User model with custom admin
admin.site.register(User, CustomUserAdmin)