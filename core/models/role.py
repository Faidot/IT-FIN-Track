"""
Role model for dynamic permission management.
"""

from django.db import models


class Role(models.Model):
    """Role model with granular permissions."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Role name (e.g., Admin, Manager, Viewer)'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of this role'
    )
    
    # Core permissions
    can_view = models.BooleanField(
        default=True,
        help_text='Can view records'
    )
    can_create = models.BooleanField(
        default=False,
        help_text='Can create new records'
    )
    can_edit = models.BooleanField(
        default=False,
        help_text='Can edit existing records'
    )
    can_delete = models.BooleanField(
        default=False,
        help_text='Can delete records (soft delete)'
    )
    can_approve = models.BooleanField(
        default=False,
        help_text='Can approve/reject expenses'
    )
    
    # Module access
    can_manage_income = models.BooleanField(
        default=False,
        help_text='Can manage income records'
    )
    can_manage_expenses = models.BooleanField(
        default=False,
        help_text='Can manage expense records'
    )
    can_manage_vendors = models.BooleanField(
        default=False,
        help_text='Can manage vendors'
    )
    can_manage_categories = models.BooleanField(
        default=False,
        help_text='Can manage categories'
    )
    can_manage_recurring_bills = models.BooleanField(
        default=False,
        help_text='Can manage recurring bills'
    )
    can_manage_income_sources = models.BooleanField(
        default=False,
        help_text='Can manage income sources'
    )
    
    # Report permissions
    can_view_reports = models.BooleanField(
        default=False,
        help_text='Can view reports dashboard'
    )
    can_view_expense_report = models.BooleanField(
        default=False,
        help_text='Can view monthly expense report'
    )
    can_view_income_report = models.BooleanField(
        default=False,
        help_text='Can view income vs expense report'
    )
    can_view_account_balance = models.BooleanField(
        default=False,
        help_text='Can view account balance report'
    )
    can_view_reimbursement_report = models.BooleanField(
        default=False,
        help_text='Can view reimbursement report'
    )
    can_view_audit_trail = models.BooleanField(
        default=False,
        help_text='Can view audit trail'
    )
    can_export_data = models.BooleanField(
        default=False,
        help_text='Can export data to Excel'
    )
    
    # Admin permissions
    can_manage_users = models.BooleanField(
        default=False,
        help_text='Can manage user accounts'
    )
    can_manage_roles = models.BooleanField(
        default=False,
        help_text='Can manage roles and permissions'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Is this role active?'
    )
    is_default = models.BooleanField(
        default=False,
        help_text='Is this the default role for new users?'
    )
    is_soft_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure only one default role
        if self.is_default:
            Role.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default_role(cls):
        """Get the default role for new users."""
        return cls.objects.filter(is_default=True, is_active=True, is_soft_deleted=False).first()
    
    @property
    def permission_count(self):
        """Count how many permissions are enabled."""
        count = 0
        permission_fields = [
            'can_view', 'can_create', 'can_edit', 'can_delete', 'can_approve',
            'can_manage_income', 'can_manage_expenses', 'can_manage_vendors',
            'can_manage_categories', 'can_manage_recurring_bills', 'can_manage_income_sources',
            'can_view_reports', 'can_view_expense_report', 'can_view_income_report',
            'can_view_account_balance', 'can_view_reimbursement_report', 'can_view_audit_trail',
            'can_export_data', 'can_manage_users', 'can_manage_roles',
        ]
        for field in permission_fields:
            if getattr(self, field, False):
                count += 1
        return count
    
    @classmethod
    def create_default_roles(cls):
        """Create default system roles if they don't exist."""
        defaults = [
            {
                'name': 'Administrator',
                'description': 'Full system access with all permissions',
                'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True, 'can_approve': True,
                'can_manage_income': True, 'can_manage_expenses': True, 'can_manage_vendors': True,
                'can_manage_categories': True, 'can_manage_recurring_bills': True, 'can_manage_income_sources': True,
                'can_view_reports': True, 'can_view_expense_report': True, 'can_view_income_report': True,
                'can_view_account_balance': True, 'can_view_reimbursement_report': True, 'can_view_audit_trail': True,
                'can_export_data': True, 'can_manage_users': True, 'can_manage_roles': True,
            },
            {
                'name': 'Manager',
                'description': 'Can view all data, approve expenses, and access reports',
                'can_view': True, 'can_create': False, 'can_edit': False, 'can_delete': False, 'can_approve': True,
                'can_manage_income': False, 'can_manage_expenses': False, 'can_manage_vendors': False,
                'can_manage_categories': False, 'can_manage_recurring_bills': False, 'can_manage_income_sources': False,
                'can_view_reports': True, 'can_view_expense_report': True, 'can_view_income_report': True,
                'can_view_account_balance': True, 'can_view_reimbursement_report': True, 'can_view_audit_trail': False,
                'can_export_data': True, 'can_manage_users': False, 'can_manage_roles': False,
            },
            {
                'name': 'IT Executive',
                'description': 'Can create and manage transactions',
                'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': False, 'can_approve': False,
                'can_manage_income': True, 'can_manage_expenses': True, 'can_manage_vendors': True,
                'can_manage_categories': False, 'can_manage_recurring_bills': True, 'can_manage_income_sources': False,
                'can_view_reports': True, 'can_view_expense_report': True, 'can_view_income_report': True,
                'can_view_account_balance': True, 'can_view_reimbursement_report': False, 'can_view_audit_trail': False,
                'can_export_data': False, 'can_manage_users': False, 'can_manage_roles': False,
            },
            {
                'name': 'Viewer',
                'description': 'Read-only access to view records',
                'can_view': True, 'can_create': False, 'can_edit': False, 'can_delete': False, 'can_approve': False,
                'can_manage_income': False, 'can_manage_expenses': False, 'can_manage_vendors': False,
                'can_manage_categories': False, 'can_manage_recurring_bills': False, 'can_manage_income_sources': False,
                'can_view_reports': False, 'can_view_expense_report': False, 'can_view_income_report': False,
                'can_view_account_balance': False, 'can_view_reimbursement_report': False, 'can_view_audit_trail': False,
                'can_export_data': False, 'can_manage_users': False, 'can_manage_roles': False,
                'is_default': True,
            },
        ]
        
        for role_data in defaults:
            cls.objects.get_or_create(name=role_data['name'], defaults=role_data)
