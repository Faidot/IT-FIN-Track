"""
Audit Log model for complete audit trail.
"""

import json
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """Complete audit trail for all actions."""
    
    class ActionType(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        SOFT_DELETE = 'soft_delete', 'Soft Delete'
        RESTORE = 'restore', 'Restore'
        VIEW = 'view', 'View'
        EXPORT = 'export', 'Export'
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        APPROVE = 'approve', 'Approve'
        REJECT = 'reject', 'Reject'
    
    # User information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        help_text='User who performed the action'
    )
    user_name = models.CharField(
        max_length=150,
        blank=True,
        help_text='Username at time of action (preserved even if user deleted)'
    )
    user_role = models.CharField(
        max_length=50,
        blank=True,
        help_text='User role at time of action'
    )
    
    # Action details
    action = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        help_text='Type of action performed'
    )
    model_name = models.CharField(
        max_length=100,
        help_text='Name of the affected model'
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID of the affected record'
    )
    object_repr = models.CharField(
        max_length=300,
        blank=True,
        help_text='String representation of the object'
    )
    
    # Change tracking
    old_values = models.JSONField(
        null=True,
        blank=True,
        help_text='Previous values (for updates)'
    )
    new_values = models.JSONField(
        null=True,
        blank=True,
        help_text='New values (for creates/updates)'
    )
    changes_summary = models.TextField(
        blank=True,
        help_text='Human-readable summary of changes'
    )
    
    # Request metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='Client IP address'
    )
    user_agent = models.TextField(
        blank=True,
        help_text='Browser/Client user agent'
    )
    request_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Request URL path'
    )
    request_method = models.CharField(
        max_length=10,
        blank=True,
        help_text='HTTP method (GET, POST, etc.)'
    )
    
    # Timestamp
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When the action occurred'
    )
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user_name} {self.action} {self.model_name} at {self.timestamp}"
    
    @property
    def action_color(self):
        """Return color for the action type."""
        colors = {
            'create': '#28A745',
            'update': '#FF6B01',
            'delete': '#DC3545',
            'soft_delete': '#DC3545',
            'restore': '#17A2B8',
            'view': '#6C757D',
            'export': '#6C757D',
            'login': '#28A745',
            'logout': '#FFC107',
            'approve': '#28A745',
            'reject': '#DC3545',
        }
        return colors.get(self.action, '#6C757D')
    
    @property
    def action_icon(self):
        """Return icon for the action type."""
        icons = {
            'create': 'fa-plus-circle',
            'update': 'fa-edit',
            'delete': 'fa-trash',
            'soft_delete': 'fa-trash-alt',
            'restore': 'fa-undo',
            'view': 'fa-eye',
            'export': 'fa-download',
            'login': 'fa-sign-in-alt',
            'logout': 'fa-sign-out-alt',
            'approve': 'fa-check-circle',
            'reject': 'fa-times-circle',
        }
        return icons.get(self.action, 'fa-circle')
    
    def get_changes_list(self):
        """Get list of field changes for display."""
        if not self.old_values or not self.new_values:
            return []
        
        changes = []
        for field, new_val in self.new_values.items():
            old_val = self.old_values.get(field)
            if old_val != new_val:
                changes.append({
                    'field': field.replace('_', ' ').title(),
                    'old': old_val,
                    'new': new_val,
                })
        return changes
    
    @classmethod
    def log_action(cls, user, action, model_name, object_id=None, object_repr='',
                   old_values=None, new_values=None, changes_summary='',
                   ip_address=None, user_agent='', request_path='', request_method=''):
        """Create an audit log entry."""
        return cls.objects.create(
            user=user,
            user_name=user.username if user else 'Anonymous',
            user_role=getattr(user, 'role', '') if user else '',
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr[:300] if object_repr else '',
            old_values=old_values,
            new_values=new_values,
            changes_summary=changes_summary,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else '',
            request_path=request_path[:500] if request_path else '',
            request_method=request_method,
        )
