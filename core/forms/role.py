"""
Forms for Role management.
"""

from django import forms
from core.models import Role


class RoleForm(forms.ModelForm):
    """Form for creating/editing roles."""
    
    class Meta:
        model = Role
        fields = [
            'name', 'description', 'is_active', 'is_default',
            # Core permissions
            'can_view', 'can_create', 'can_edit', 'can_delete', 'can_approve',
            # Module access
            'can_manage_income', 'can_manage_expenses', 'can_manage_vendors',
            'can_manage_categories', 'can_manage_recurring_bills', 'can_manage_income_sources',
            # Report permissions
            'can_view_reports', 'can_view_expense_report', 'can_view_income_report',
            'can_view_account_balance', 'can_view_reimbursement_report', 'can_view_audit_trail',
            'can_export_data',
            # Admin permissions
            'can_manage_users', 'can_manage_roles',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Role name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Role description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Core permissions
            'can_view': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_create': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_edit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_delete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_approve': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Module access
            'can_manage_income': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_expenses': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_vendors': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_categories': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_recurring_bills': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_income_sources': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Report permissions
            'can_view_reports': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_expense_report': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_income_report': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_account_balance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_reimbursement_report': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_audit_trail': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_export_data': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Admin permissions
            'can_manage_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_roles': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
