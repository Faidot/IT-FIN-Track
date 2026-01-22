"""
Income Source model for defining custom income sources.
"""

from django.db import models
from django.db.models import Sum, Count


class IncomeSource(models.Model):
    """Define custom income sources (like Vendor for expenses)."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Name of the income source'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of this income source'
    )
    icon = models.CharField(
        max_length=50,
        default='fa-money-bill',
        help_text='Font Awesome icon class (e.g., fa-building)'
    )
    color = models.CharField(
        max_length=7,
        default='#FF6B01',
        help_text='Color for this source (hex code)'
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        help_text='Contact person for this source'
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone number'
    )
    contact_email = models.EmailField(
        blank=True,
        help_text='Contact email'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this source is active'
    )
    is_soft_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Income Source'
        verbose_name_plural = 'Income Sources'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def income_count(self):
        """Count of incomes from this source."""
        return self.incomes.filter(is_soft_deleted=False).count()
    
    @property
    def total_income(self):
        """Total income from this source."""
        result = self.incomes.filter(is_soft_deleted=False).aggregate(
            total=Sum('amount')
        )['total']
        return result or 0
    
    @property
    def pending_reimbursement(self):
        """Pending reimbursement amount from this source."""
        result = self.incomes.filter(
            is_soft_deleted=False,
            is_reimbursable=True,
            reimbursed=False
        ).aggregate(total=Sum('amount'))['total']
        return result or 0
    
    @classmethod
    def get_default_sources(cls):
        """Get default income sources to seed the database."""
        return [
            {
                'name': 'Company Accounts',
                'icon': 'fa-building',
                'color': '#4E4E4E',
                'description': 'Funds from company accounts department'
            },
            {
                'name': 'Manager Advance',
                'icon': 'fa-user-tie',
                'color': '#17A2B8',
                'description': 'Advance cash from manager for purchases'
            },
            {
                'name': 'Personal Money',
                'icon': 'fa-wallet',
                'color': '#FFC107',
                'description': 'Employee personal money used for work'
            },
            {
                'name': 'Vendor Refund',
                'icon': 'fa-undo',
                'color': '#28A745',
                'description': 'Refunds received from vendors'
            },
            {
                'name': 'Project Fund',
                'icon': 'fa-project-diagram',
                'color': '#6F42C1',
                'description': 'Specific project or client funded amount'
            },
            {
                'name': 'Other',
                'icon': 'fa-plus-circle',
                'color': '#FF6B01',
                'description': 'Miscellaneous income sources'
            },
        ]
