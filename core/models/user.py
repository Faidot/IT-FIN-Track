"""
Custom User model for IT FIN Track.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with role-based access control."""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        EXECUTIVE = 'executive', 'IT Executive'
        ACCOUNTANT = 'accountant', 'Accountant'
        MANAGER = 'manager', 'Manager'
        VIEWER = 'viewer', 'Viewer'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        help_text='User role determines access permissions'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        default='IT',
        help_text='Department the user belongs to'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone number'
    )
    is_soft_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag - never lose data'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_executive(self):
        return self.role == self.Role.EXECUTIVE
    
    @property
    def is_accountant(self):
        return self.role == self.Role.ACCOUNTANT
    
    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER
    
    @property
    def is_viewer(self):
        return self.role == self.Role.VIEWER
    
    @property
    def can_edit(self):
        """Check if user can create/edit transactions."""
        return self.role in [self.Role.ADMIN, self.Role.EXECUTIVE, self.Role.ACCOUNTANT]
    
    @property
    def can_approve(self):
        """Check if user can approve transactions."""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER]
    
    @property
    def can_delete(self):
        """Check if user can delete records."""
        return self.role == self.Role.ADMIN
    
    @property
    def can_view_reports(self):
        """Check if user can view reports."""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER, self.Role.ACCOUNTANT, self.Role.EXECUTIVE]
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role == self.Role.ADMIN
    
    @property
    def can_manage_roles(self):
        """Check if user can manage roles (admin only)."""
        return self.role == self.Role.ADMIN
