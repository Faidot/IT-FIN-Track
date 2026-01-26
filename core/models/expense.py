"""
Expense and ExpenseBill models for tracking all expenses.
"""

import os
from django.db import models
from django.conf import settings
from decimal import Decimal


def bill_upload_path(instance, filename):
    """Generate upload path for expense bills."""
    ext = filename.split('.')[-1]
    expense_id = instance.expense.id if instance.expense_id else 'new'
    new_filename = f"expense_{expense_id}_{instance.id or 'new'}.{ext}"
    return os.path.join('bills', str(instance.expense.date.year), str(instance.expense.date.month), new_filename)


class Expense(models.Model):
    """Track all IT expenses with evidence."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    category = models.ForeignKey(
        'Category',
        on_delete=models.PROTECT,
        related_name='expenses',
        help_text='Expense category'
    )
    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.PROTECT,
        related_name='expenses',
        null=True,
        blank=True,
        help_text='Vendor/Supplier'
    )
    linked_income = models.ForeignKey(
        'Income',
        on_delete=models.SET_NULL,
        related_name='linked_expenses',
        null=True,
        blank=True,
        help_text='Income source for this expense'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Expense amount'
    )
    date = models.DateField(
        help_text='Date of expense'
    )
    description = models.TextField(
        help_text='Description of the expense'
    )
    purpose = models.CharField(
        max_length=300,
        blank=True,
        help_text='Purpose or project for this expense'
    )
    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Invoice/Bill number'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text='Approval status'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses_approved',
        help_text='User who approved this expense'
    )
    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date and time of approval'
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection (if rejected)'
    )
    
    # Tracking fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='expenses_created',
        help_text='User who created this record'
    )
    is_soft_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        amount = Decimal(str(self.amount)) if self.amount else Decimal('0')
        return f"{self.category.name} - Rs. {amount:,.2f} ({self.date})"
    
    @property
    def status_badge_class(self):
        """Return Bootstrap badge class for status."""
        classes = {
            'pending': 'bg-warning text-dark',
            'approved': 'bg-success',
            'rejected': 'bg-danger',
        }
        return classes.get(self.status, 'bg-secondary')
    
    @property
    def has_bills(self):
        """Check if expense has attached bills."""
        return self.bills.exists()
    
    @property
    def bills_count(self):
        """Count of attached bills."""
        return self.bills.count()
    
    @classmethod
    def get_total_expenses(cls, start_date=None, end_date=None, category=None):
        """Get total expenses for a date range and optionally by category."""
        queryset = cls.objects.filter(is_soft_deleted=False)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if category:
            queryset = queryset.filter(category=category)
        return queryset.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    @classmethod
    def get_pending_expenses(cls):
        """Get expenses pending approval."""
        return cls.objects.filter(
            is_soft_deleted=False,
            status=cls.Status.PENDING
        )
    
    @classmethod
    def get_category_breakdown(cls, start_date=None, end_date=None):
        """Get expense breakdown by category."""
        queryset = cls.objects.filter(is_soft_deleted=False)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        return queryset.values(
            'category__name', 'category__color', 'category__icon'
        ).annotate(
            total=models.Sum('amount'),
            count=models.Count('id')
        ).order_by('-total')


class ExpenseBill(models.Model):
    """Multiple bills/invoices per expense."""
    
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='bills',
        help_text='Related expense'
    )
    file = models.FileField(
        upload_to='bills/%Y/%m/',
        help_text='Bill/Invoice file (PDF, JPG, PNG)'
    )
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        help_text='Original filename'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text='Bill description'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        help_text='User who uploaded this bill'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Expense Bill'
        verbose_name_plural = 'Expense Bills'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Bill for {self.expense} - {self.original_filename}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)
    
    @property
    def file_extension(self):
        """Get file extension."""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''
    
    @property
    def is_image(self):
        """Check if file is an image."""
        return self.file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    @property
    def is_pdf(self):
        """Check if file is a PDF."""
        return self.file_extension == '.pdf'
