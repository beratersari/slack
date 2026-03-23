"""
Admin configuration for core app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from core.models import User, UserType


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for User model.
    """
    list_display = [
        'email', 'username', 'user_type', 'first_name', 'last_name',
        'is_active', 'is_staff', 'created_at'
    ]
    list_filter = ['user_type', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'avatar', 'phone', 
                       'job_title', 'department', 'status_message', 'timezone')
        }),
        (_('User Type'), {'fields': ('user_type',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 
                       'user_type', 'first_name', 'last_name'),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_admin():
            return qs
        # Non-admin users can only see their own record
        return qs.filter(id=request.user.id)
    
    def has_view_permission(self, request, obj=None):
        if obj is None:
            return True
        return request.user.is_admin() or obj == request.user
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return request.user.is_admin() or obj == request.user
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_admin()
