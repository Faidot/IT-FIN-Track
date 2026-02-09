"""
Recurring Bill models for IT FIN Track.
Manages recurring expenses like Internet, Hosting, etc.
"""

from django.db import models
from django.conf import settings
from decimal import Decimal
from datetime import date, timedelta
from calendar import monthrange


def add_months(source_date, months):
    """Add months to a date without dateutil."""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    # Get max day for target month
    max_day = monthrange(year, month)[1]
    day = min(source_date.day, max_day)
    return date(year, month, day)


class RecurringBill(models.Model):
    """Recurring bill/subscription management."""
    
    class Frequency(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        QUARTERLY = 'quarterly', 'Quarterly'
        YEARLY = 'yearly', 'Yearly'
    
    name = models.CharField(
        max_length=200,
        help_text='Bill name (e.g., Internet, Hosting)'
    )
    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.PROTECT,
        related_name='recurring_bills',
        null=True,
        blank=True,
        help_text='Service provider'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.PROTECT,
        related_name='recurring_bills',
        help_text='Expense category'
    )
    base_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Standard billing amount'
    )
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.MONTHLY,
        help_text='Billing frequency'
    )
    billing_day = models.PositiveIntegerField(
        default=1,
        help_text='Day of month bill is due (1-28)'
    )
    start_date = models.DateField(
        help_text='When this recurring bill started'
    )
    description = models.TextField(
        blank=True,
        help_text='Additional details'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Is this bill still active'
    )
    
    # Tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='bills_created'
    )
    is_soft_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Recurring Bill'
        verbose_name_plural = 'Recurring Bills'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - Rs. {self.base_amount:,.0f}/{self.get_frequency_display()}"
    
    def get_next_due_date(self):
        """Calculate the next due date based on frequency."""
        today = date.today()
        
        # Find the last payment
        last_payment = self.payments.filter(status='paid').order_by('-period_end').first()
        
        if last_payment:
            base_date = last_payment.period_end
        else:
            base_date = self.start_date
        
        # Calculate next due date
        if self.frequency == self.Frequency.MONTHLY:
            next_date = add_months(base_date, 1)
        elif self.frequency == self.Frequency.QUARTERLY:
            next_date = add_months(base_date, 3)
        else:  # yearly
            next_date = add_months(base_date, 12)
        
        # Adjust to billing day
        max_day = monthrange(next_date.year, next_date.month)[1]
        target_day = min(self.billing_day, max_day)
        next_date = next_date.replace(day=target_day)
        
        return next_date
    
    def get_current_period(self):
        """Get current billing period dates."""
        next_due = self.get_next_due_date()
        
        if self.frequency == self.Frequency.MONTHLY:
            period_start = add_months(next_due, -1)
        elif self.frequency == self.Frequency.QUARTERLY:
            period_start = add_months(next_due, -3)
        else:
            period_start = add_months(next_due, -12)
        
        return period_start, next_due
    
    @property
    def is_overdue(self):
        """Check if current payment is overdue."""
        pending = self.payments.filter(status='pending').first()
        if pending:
            return pending.due_date < date.today()
        return self.get_next_due_date() < date.today()
    
    @property
    def pending_payment(self):
        """Get current pending payment if any."""
        return self.payments.filter(status='pending').first()


class BillPayment(models.Model):
    """Individual payment for a recurring bill."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
    
    class PaymentType(models.TextChoices):
        IT_PAYMENT = 'it_payment', 'IT Payment (from IT Budget)'
        ACCOUNTS_PAY = 'accounts_pay', 'Accounts Direct Pay (to Vendor)'
    
    bill = models.ForeignKey(
        RecurringBill,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    period_start = models.DateField(
        help_text='Billing period start'
    )
    period_end = models.DateField(
        help_text='Billing period end'
    )
    due_date = models.DateField(
        help_text='Payment due date'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Amount for this period'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.IT_PAYMENT,
        help_text='Who handles the payment'
    )
    linked_income = models.ForeignKey(
        'Income',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bill_payments',
        help_text='Income source for this payment'
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date payment was made'
    )
    expense = models.OneToOneField(
        'Expense',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bill_payment',
        help_text='Linked expense record'
    )
    notes = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='bill_payments_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bill Payment'
        verbose_name_plural = 'Bill Payments'
        ordering = ['-due_date']
    
    def __str__(self):
        return f"{self.bill.name} - {self.period_start} to {self.period_end}"
    
    @property
    def is_overdue(self):
        return self.status == 'pending' and self.due_date < date.today()
    
    @property
    def is_accounts_pay(self):
        return self.payment_type == self.PaymentType.ACCOUNTS_PAY

