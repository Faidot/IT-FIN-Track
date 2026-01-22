"""
Admin configuration for IT FIN Track.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core.models import User, Category, Vendor, IncomeSource, Income, Expense, ExpenseBill, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'department', 'phone', 'is_soft_deleted')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'department', 'phone')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_soft_deleted']
    search_fields = ['name', 'description']


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_active']
    list_filter = ['is_active', 'is_soft_deleted']
    search_fields = ['name', 'contact_person', 'email']


@admin.register(IncomeSource)
class IncomeSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_soft_deleted']
    search_fields = ['name', 'description', 'contact_person']


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['source', 'amount', 'date', 'payment_mode', 'created_by', 'created_at']
    list_filter = ['source', 'payment_mode', 'is_reimbursable', 'reimbursed', 'is_soft_deleted']
    search_fields = ['source_detail', 'reference_number', 'description']
    date_hierarchy = 'date'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'vendor', 'amount', 'date', 'status', 'created_by', 'created_at']
    list_filter = ['category', 'status', 'is_soft_deleted']
    search_fields = ['description', 'purpose', 'invoice_number']
    date_hierarchy = 'date'


@admin.register(ExpenseBill)
class ExpenseBillAdmin(admin.ModelAdmin):
    list_display = ['expense', 'original_filename', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'action', 'model_name', 'object_id', 'timestamp', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user_name', 'changes_summary', 'object_repr']
    date_hierarchy = 'timestamp'
    readonly_fields = ['user', 'user_name', 'user_role', 'action', 'model_name', 'object_id', 
                      'object_repr', 'old_values', 'new_values', 'changes_summary',
                      'ip_address', 'user_agent', 'request_path', 'request_method', 'timestamp']
