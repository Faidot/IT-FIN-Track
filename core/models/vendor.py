"""
Vendor model for tracking suppliers and service providers.
"""

from django.db import models


class Vendor(models.Model):
    """Vendor/Supplier information for expense tracking."""
    
    name = models.CharField(
        max_length=200,
        help_text='Vendor/Company name'
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        help_text='Primary contact person'
    )
    email = models.EmailField(
        blank=True,
        help_text='Contact email'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone number'
    )
    address = models.TextField(
        blank=True,
        help_text='Vendor address'
    )
    gst_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='GST/Tax registration number'
    )
    bank_details = models.TextField(
        blank=True,
        help_text='Bank account details for payments'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the vendor'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Is this vendor currently active?'
    )
    is_soft_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def total_expenses(self):
        """Calculate total expenses from this vendor."""
        return self.expenses.filter(is_soft_deleted=False).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    @property
    def transaction_count(self):
        """Count of transactions with this vendor."""
        return self.expenses.filter(is_soft_deleted=False).count()
