"""
Recurring Bills views for IT FIN Track.
Manage recurring IT department expenses like Internet, Hosting, etc.
"""

from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum

from core.models import RecurringBill, BillPayment, Expense, Category, Vendor


@login_required
def bill_list(request):
    """List all recurring bills with status."""
    bills = RecurringBill.objects.filter(is_soft_deleted=False).select_related(
        'category', 'vendor', 'created_by'
    ).prefetch_related('payments')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        bills = bills.filter(is_active=True)
    elif status_filter == 'inactive':
        bills = bills.filter(is_active=False)
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        bills = bills.filter(
            Q(name__icontains=search) |
            Q(vendor__name__icontains=search)
        )
    
    # Calculate pending and paid totals
    today = date.today()
    pending_total = BillPayment.objects.filter(
        bill__is_soft_deleted=False,
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    paid_this_month = BillPayment.objects.filter(
        bill__is_soft_deleted=False,
        status='paid',
        paid_date__year=today.year,
        paid_date__month=today.month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    context = {
        'bills': bills,
        'pending_total': pending_total,
        'paid_this_month': paid_this_month,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'core/bills/list.html', context)


@login_required
def bill_create(request):
    """Create a new recurring bill."""
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to create bills.')
        return redirect('core:bill_list')
    
    categories = Category.objects.filter(is_soft_deleted=False, is_active=True)
    vendors = Vendor.objects.filter(is_soft_deleted=False, is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name', '')
        vendor_id = request.POST.get('vendor', '')
        category_id = request.POST.get('category', '')
        base_amount = request.POST.get('base_amount', '0')
        frequency = request.POST.get('frequency', 'monthly')
        billing_day = request.POST.get('billing_day', '1')
        start_date = request.POST.get('start_date', '')
        description = request.POST.get('description', '')
        
        if name and category_id and base_amount and start_date:
            bill = RecurringBill.objects.create(
                name=name,
                vendor_id=vendor_id if vendor_id else None,
                category_id=category_id,
                base_amount=Decimal(base_amount),
                frequency=frequency,
                billing_day=int(billing_day),
                start_date=start_date,
                description=description,
                created_by=request.user
            )
            
            # Create first pending payment
            create_pending_payment(bill, request.user)
            
            messages.success(request, f'Recurring bill "{name}" created successfully!')
            return redirect('core:bill_list')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'core/bills/form.html', {
        'categories': categories,
        'vendors': vendors,
        'title': 'Add Recurring Bill',
        'action': 'Create',
        'frequencies': RecurringBill.Frequency.choices,
    })


@login_required
def bill_edit(request, pk):
    """Edit a recurring bill."""
    bill = get_object_or_404(RecurringBill, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to edit bills.')
        return redirect('core:bill_list')
    
    categories = Category.objects.filter(is_soft_deleted=False, is_active=True)
    vendors = Vendor.objects.filter(is_soft_deleted=False, is_active=True)
    
    if request.method == 'POST':
        bill.name = request.POST.get('name', bill.name)
        vendor_id = request.POST.get('vendor', '')
        bill.vendor_id = vendor_id if vendor_id else None
        bill.category_id = request.POST.get('category', bill.category_id)
        bill.base_amount = Decimal(request.POST.get('base_amount', bill.base_amount))
        bill.frequency = request.POST.get('frequency', bill.frequency)
        bill.billing_day = int(request.POST.get('billing_day', bill.billing_day))
        bill.description = request.POST.get('description', bill.description)
        bill.is_active = request.POST.get('is_active') == 'on'
        bill.save()
        
        messages.success(request, f'Bill "{bill.name}" updated successfully!')
        return redirect('core:bill_list')
    
    return render(request, 'core/bills/form.html', {
        'bill': bill,
        'categories': categories,
        'vendors': vendors,
        'title': 'Edit Recurring Bill',
        'action': 'Update',
        'frequencies': RecurringBill.Frequency.choices,
    })


@login_required
def bill_detail(request, pk):
    """View bill details and payment history."""
    bill = get_object_or_404(
        RecurringBill.objects.select_related('category', 'vendor', 'created_by'),
        pk=pk,
        is_soft_deleted=False
    )
    
    payments = bill.payments.select_related('expense', 'created_by').order_by('-due_date')
    
    # Stats
    total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    payments_count = payments.filter(status='paid').count()
    
    return render(request, 'core/bills/detail.html', {
        'bill': bill,
        'payments': payments,
        'total_paid': total_paid,
        'payments_count': payments_count,
    })


@login_required
def bill_delete(request, pk):
    """Soft delete a recurring bill."""
    bill = get_object_or_404(RecurringBill, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_delete:
        messages.error(request, 'You do not have permission to delete bills.')
        return redirect('core:bill_list')
    
    if request.method == 'POST':
        bill.is_soft_deleted = True
        bill.save()
        messages.success(request, f'Bill "{bill.name}" deleted successfully!')
        return redirect('core:bill_list')
    
    return render(request, 'core/bills/confirm_delete.html', {'bill': bill})


@login_required
def bill_pay(request, pk):
    """Mark a bill payment as paid and create expense."""
    bill = get_object_or_404(RecurringBill, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to record payments.')
        return redirect('core:bill_detail', pk=pk)
    
    # Get or create pending payment
    payment = bill.pending_payment
    if not payment:
        payment = create_pending_payment(bill, request.user)
    
    if request.method == 'POST':
        # Get payment details from form
        amount = Decimal(request.POST.get('amount', payment.amount))
        paid_date = request.POST.get('paid_date', date.today().isoformat())
        notes = request.POST.get('notes', '')
        
        # Create expense record
        expense = Expense.objects.create(
            category=bill.category,
            vendor=bill.vendor,
            amount=amount,
            date=paid_date,
            description=f"{bill.name} - {payment.period_start} to {payment.period_end}",
            purpose=f"Recurring bill payment: {bill.name}",
            status='pending',  # Will need approval
            created_by=request.user
        )
        
        # Update payment
        payment.amount = amount
        payment.paid_date = paid_date
        payment.status = 'paid'
        payment.expense = expense
        payment.notes = notes
        payment.save()
        
        # Create next pending payment
        create_pending_payment(bill, request.user)
        
        messages.success(request, f'Payment for "{bill.name}" recorded! Expense created pending approval.')
        return redirect('core:bill_detail', pk=pk)
    
    return render(request, 'core/bills/pay_form.html', {
        'bill': bill,
        'payment': payment,
    })


@login_required
def bill_generate_payment(request, pk):
    """Generate a new pending payment for a bill."""
    bill = get_object_or_404(RecurringBill, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_edit:
        messages.error(request, 'Permission denied.')
        return redirect('core:bill_detail', pk=pk)
    
    if not bill.pending_payment:
        create_pending_payment(bill, request.user)
        messages.success(request, 'New payment period generated!')
    else:
        messages.warning(request, 'There is already a pending payment for this bill.')
    
    return redirect('core:bill_detail', pk=pk)


def create_pending_payment(bill, user):
    """Helper: Create a pending payment for the next billing period."""
    today = date.today()
    
    # Get last payment to determine period
    last_payment = bill.payments.order_by('-period_end').first()
    
    if last_payment:
        period_start = last_payment.period_end
    else:
        period_start = bill.start_date
    
    # Calculate period end based on frequency
    if bill.frequency == RecurringBill.Frequency.MONTHLY:
        period_end = period_start + relativedelta(months=1)
    elif bill.frequency == RecurringBill.Frequency.QUARTERLY:
        period_end = period_start + relativedelta(months=3)
    else:
        period_end = period_start + relativedelta(years=1)
    
    # Due date is billing_day of the end period
    try:
        due_date = period_end.replace(day=bill.billing_day)
    except ValueError:
        due_date = period_end.replace(day=28)
    
    payment = BillPayment.objects.create(
        bill=bill,
        period_start=period_start,
        period_end=period_end,
        due_date=due_date,
        amount=bill.base_amount,
        status='pending',
        created_by=user
    )
    
    return payment
