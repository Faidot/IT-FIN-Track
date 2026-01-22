"""
Ledger model for personal money tracking and reimbursements.
"""

from django.db import models
from django.conf import settings
from decimal import Decimal


class Ledger(models.Model):
    """Personal money ledger for tracking advances and reimbursements."""
    
    class LedgerType(models.TextChoices):
        PERSONAL = 'personal', 'Personal Money'
        MANAGER = 'manager', 'Manager Advance'
        EMPLOYEE = 'employee', 'Employee Advance'
    
    name = models.CharField(
        max_length=100,
        help_text='Ledger name (e.g., "My Personal Fund", "Manager Advance")'
    )
    ledger_type = models.CharField(
        max_length=20,
        choices=LedgerType.choices,
        default=LedgerType.PERSONAL,
        help_text='Type of ledger'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ledgers',
        help_text='Owner of this ledger'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of this ledger'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Is this ledger currently active?'
    )
    is_soft_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ledger'
        verbose_name_plural = 'Ledgers'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_ledger_type_display()})"
    
    @property
    def total_advanced(self):
        """Total amount advanced to the ledger."""
        return self.entries.filter(
            is_soft_deleted=False,
            entry_type=LedgerEntry.EntryType.ADVANCE
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    @property
    def total_spent(self):
        """Total amount spent from the ledger."""
        return self.entries.filter(
            is_soft_deleted=False,
            entry_type=LedgerEntry.EntryType.EXPENSE
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    @property
    def total_reimbursed(self):
        """Total amount reimbursed."""
        return self.entries.filter(
            is_soft_deleted=False,
            entry_type=LedgerEntry.EntryType.REIMBURSEMENT
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    @property
    def current_balance(self):
        """Current balance (Advanced - Spent)."""
        return self.total_advanced - self.total_spent
    
    @property
    def pending_reimbursement(self):
        """Amount pending reimbursement (Spent - Reimbursed)."""
        return self.total_spent - self.total_reimbursed


class LedgerEntry(models.Model):
    """Individual entries in a ledger."""
    
    class EntryType(models.TextChoices):
        ADVANCE = 'advance', 'Advance Received'
        EXPENSE = 'expense', 'Expense Made'
        REIMBURSEMENT = 'reimbursement', 'Reimbursement Received'
        RETURN = 'return', 'Amount Returned'
    
    ledger = models.ForeignKey(
        Ledger,
        on_delete=models.CASCADE,
        related_name='entries',
        help_text='Related ledger'
    )
    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices,
        help_text='Type of entry'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Entry amount'
    )
    date = models.DateField(
        help_text='Date of entry'
    )
    description = models.TextField(
        help_text='Description of this entry'
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text='Reference number or linked transaction'
    )
    linked_expense = models.ForeignKey(
        'Expense',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ledger_entries',
        help_text='Linked expense (if applicable)'
    )
    
    # Tracking fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ledger_entries_created',
        help_text='User who created this entry'
    )
    is_soft_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ledger Entry'
        verbose_name_plural = 'Ledger Entries'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.get_entry_type_display()} - Rs. {self.amount:,.2f} ({self.date})"
    
    @property
    def entry_color(self):
        """Return color based on entry type."""
        colors = {
            'advance': '#28A745',
            'expense': '#DC3545',
            'reimbursement': '#17A2B8',
            'return': '#FFC107',
        }
        return colors.get(self.entry_type, '#6C757D')
    
    @property
    def entry_icon(self):
        """Return icon based on entry type."""
        icons = {
            'advance': 'fa-arrow-down',
            'expense': 'fa-arrow-up',
            'reimbursement': 'fa-undo',
            'return': 'fa-exchange-alt',
        }
        return icons.get(self.entry_type, 'fa-circle')
