"""
Income model for tracking all income sources.
"""

from django.db import models
from django.conf import settings
from decimal import Decimal


class Income(models.Model):
    """Track all income sources for IT department."""
    
    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        BANK = 'bank', 'Bank Transfer'
        ONLINE = 'online', 'Online Payment'
        CHEQUE = 'cheque', 'Cheque'
    
    # Link to IncomeSource model (like Vendor for expenses)
    source = models.ForeignKey(
        'IncomeSource',
        on_delete=models.PROTECT,
        related_name='incomes',
        help_text='Source of the income'
    )
    source_detail = models.CharField(
        max_length=200,
        blank=True,
        help_text='Additional details about the source (e.g., person name)'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Amount received'
    )
    date = models.DateField(
        help_text='Date of receiving the amount'
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Reference number (voucher, transaction ID, etc.)'
    )
    payment_mode = models.CharField(
        max_length=20,
        choices=PaymentMode.choices,
        default=PaymentMode.CASH,
        help_text='Mode of payment'
    )
    project = models.CharField(
        max_length=200,
        blank=True,
        help_text='Linked project or purpose (optional)'
    )
    description = models.TextField(
        blank=True,
        help_text='Description or notes about this income'
    )
    is_reimbursable = models.BooleanField(
        default=False,
        help_text='Is this amount to be reimbursed later?'
    )
    reimbursed = models.BooleanField(
        default=False,
        help_text='Has this amount been reimbursed?'
    )
    reimbursed_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when reimbursement was received'
    )
    
    # Tracking fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='incomes_created',
        help_text='User who created this record'
    )
    is_soft_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Income'
        verbose_name_plural = 'Incomes'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.source.name} - Rs. {self.amount:,.2f} ({self.date})"
    
    @property
    def source_icon(self):
        """Return Font Awesome icon for the source."""
        return self.source.icon if self.source else 'fa-dollar-sign'
    
    @property
    def source_color(self):
        """Return color for the source."""
        return self.source.color if self.source else '#FF6B01'
    
    @property
    def spent_amount(self):
        """Calculate amount spent from this income."""
        return self.linked_expenses.filter(
            is_soft_deleted=False
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
    
    @property
    def remaining_amount(self):
        """Calculate remaining balance from this income."""
        return self.amount - self.spent_amount
    
    @classmethod
    def get_total_income(cls, start_date=None, end_date=None):
        """Get total income for a date range."""
        queryset = cls.objects.filter(is_soft_deleted=False)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        return queryset.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    @classmethod
    def get_pending_reimbursements(cls):
        """Get incomes pending reimbursement."""
        return cls.objects.filter(
            is_soft_deleted=False,
            is_reimbursable=True,
            reimbursed=False
        )
