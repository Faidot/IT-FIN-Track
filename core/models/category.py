"""
Category model for expense types.
"""

from django.db import models


class Category(models.Model):
    """Expense categories for organizing IT expenses."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Category name'
    )
    description = models.TextField(
        blank=True,
        help_text='Category description'
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        default='fa-folder',
        help_text='Font Awesome icon class'
    )
    color = models.CharField(
        max_length=7,
        default='#FF6B01',
        help_text='Category color (hex code)'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Is this category currently active?'
    )
    is_soft_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_default_categories(cls):
        """Return default IT expense categories."""
        return [
            {'name': 'IT Accessories', 'icon': 'fa-mouse', 'description': 'Mouse, headset, cables, etc.'},
            {'name': 'Systems', 'icon': 'fa-desktop', 'description': 'PCs, laptops, workstations'},
            {'name': 'Repairs & Maintenance', 'icon': 'fa-wrench', 'description': 'Repair and maintenance costs'},
            {'name': 'Software & Licenses', 'icon': 'fa-compact-disc', 'description': 'Software purchases and licenses'},
            {'name': 'Networking', 'icon': 'fa-network-wired', 'description': 'Networking equipment and services'},
            {'name': 'Office Supplies', 'icon': 'fa-box', 'description': 'General office supplies'},
            {'name': 'Cloud Services', 'icon': 'fa-cloud', 'description': 'Cloud hosting and services'},
            {'name': 'Security', 'icon': 'fa-shield-alt', 'description': 'Security software and equipment'},
            {'name': 'Other', 'icon': 'fa-ellipsis-h', 'description': 'Miscellaneous expenses'},
        ]
