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
    current_month = today.month
    current_year = today.year
    
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
    
    # Add month-wise payment status to each bill
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for bill in bills:
        # Get last 6 months of payments (track by period_start = billing month)
        bill.recent_payments = []
        for i in range(5, -1, -1):
            month = current_month - i
            year = current_year
            if month <= 0:
                month += 12
                year -= 1
            
            # Check if there's a paid payment for this BILLING PERIOD month (period_start)
            payment = bill.payments.filter(
                period_start__year=year,
                period_start__month=month,
                status='paid'
            ).first()
            
            # Check for pending payment for this billing month
            pending_payment = bill.payments.filter(
                period_start__year=year,
                period_start__month=month,
                status='pending'
            ).first()
            
            bill.recent_payments.append({
                'month': month_names[month - 1],
                'year': year,
                'paid': payment is not None,
                'pending': pending_payment is not None,
                'amount': payment.amount if payment else None,
                'is_current': month == current_month and year == current_year,
                'is_overdue': pending_payment.is_overdue if pending_payment else False
            })
        
        # Current month status (by billing period month)
        bill.current_month_paid = bill.payments.filter(
            period_start__year=current_year,
            period_start__month=current_month,
            status='paid'
        ).exists()
    
    context = {
        'bills': bills,
        'pending_total': pending_total,
        'paid_this_month': paid_this_month,
        'status_filter': status_filter,
        'search': search,
        'current_month_name': month_names[current_month - 1],
        'current_year': current_year,
    }
    
    return render(request, 'core/bills/list.html', context)


@login_required
def bill_create(request):
    """Create a new recurring bill."""
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to create bills.')
        return redirect('core:recurring_bill_list')
    
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
        is_active = request.POST.get('is_active') == 'on'
        
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
                is_active=is_active,
                created_by=request.user
            )
            
            # Create first pending payment only if active
            if is_active:
                create_pending_payment(bill, request.user)
            
            messages.success(request, f'Recurring bill "{name}" created successfully!')
            return redirect('core:recurring_bill_list')
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
        return redirect('core:recurring_bill_list')
    
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
        return redirect('core:recurring_bill_list')
    
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
        return redirect('core:recurring_bill_list')
    
    if request.method == 'POST':
        bill.is_soft_deleted = True
        bill.save()
        messages.success(request, f'Bill "{bill.name}" deleted successfully!')
        return redirect('core:recurring_bill_list')
    
    return render(request, 'core/bills/confirm_delete.html', {'bill': bill})


@login_required
def bill_pay(request, pk):
    """Mark a bill payment as paid and create expense."""
    bill = get_object_or_404(RecurringBill, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to record payments.')
        return redirect('core:recurring_bill_detail', pk=pk)
    
    # Get or create pending payment
    payment = bill.pending_payment
    if not payment:
        payment = create_pending_payment(bill, request.user)
    
    # Get available income sources
    from core.models import Income
    incomes = Income.objects.filter(is_soft_deleted=False).order_by('-date')
    
    if request.method == 'POST':
        # Get payment details from form
        amount = Decimal(request.POST.get('amount', payment.amount))
        paid_date = request.POST.get('paid_date', date.today().isoformat())
        notes = request.POST.get('notes', '')
        payment_type = request.POST.get('payment_type', 'it_payment')
        linked_income_id = request.POST.get('linked_income', '')
        
        # Update payment fields
        payment.amount = amount
        payment.paid_date = paid_date
        payment.payment_type = payment_type
        payment.notes = notes
        
        if linked_income_id:
            payment.linked_income_id = linked_income_id
        
        if payment_type == 'accounts_pay':
            # Accounts Pay - No expense created, just mark as paid
            payment.status = 'paid'
            payment.save()
            
            # Create next pending payment
            create_pending_payment(bill, request.user)
            
            messages.success(request, f'Payment for "{bill.name}" marked as Accounts Direct Pay (no IT expense created).')
            return redirect('core:recurring_bill_detail', pk=pk)
        else:
            # IT Payment - Create expense record
            expense = Expense.objects.create(
                category=bill.category,
                vendor=bill.vendor,
                amount=amount,
                date=paid_date,
                description=f"{bill.name} - {payment.period_start} to {payment.period_end}",
                purpose=f"Recurring bill payment: {bill.name}",
                linked_income_id=linked_income_id if linked_income_id else None,
                status='pending',  # Will need approval
                created_by=request.user
            )
            
            # Update payment
            payment.status = 'paid'
            payment.expense = expense
            payment.save()
            
            # Create next pending payment
            create_pending_payment(bill, request.user)
            
            messages.success(request, f'Payment for "{bill.name}" recorded! Expense created pending approval.')
            return redirect('core:recurring_bill_detail', pk=pk)
    
    return render(request, 'core/bills/pay_form.html', {
        'bill': bill,
        'payment': payment,
        'incomes': incomes,
        'payment_types': BillPayment.PaymentType.choices,
    })


@login_required
def bill_generate_payment(request, pk):
    """Generate a new pending payment for a bill."""
    bill = get_object_or_404(RecurringBill, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_edit:
        messages.error(request, 'Permission denied.')
        return redirect('core:recurring_bill_detail', pk=pk)
    
    if not bill.pending_payment:
        create_pending_payment(bill, request.user)
        messages.success(request, 'New payment period generated!')
    else:
        messages.warning(request, 'There is already a pending payment for this bill.')
    
    return redirect('core:recurring_bill_detail', pk=pk)


def create_pending_payment(bill, user):
    """Helper: Create a pending payment for the next billing period."""
    today = date.today()
    
    # Get last payment to determine period
    last_payment = bill.payments.order_by('-period_end').first()
    
    if last_payment:
        period_start = last_payment.period_end
    else:
        period_start = bill.start_date
    
    # Ensure period_start is a date object (not a string)
    if isinstance(period_start, str):
        from datetime import datetime
        period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
    
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


@login_required
def month_detail(request):
    """API endpoint to get month payment details for a bill."""
    from django.http import JsonResponse
    import logging

    logger = logging.getLogger(__name__)

    try:
        month_name = request.GET.get('month', '')
        year_str = request.GET.get('year', str(date.today().year))
        bill_id = request.GET.get('bill_id', '')

        # Validate inputs
        if not month_name or not bill_id:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)

        try:
            year = int(year_str)
        except ValueError:
            year = date.today().year

        # Convert month name to number
        month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                     'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        month = month_map.get(month_name, 1)

        try:
            bill = RecurringBill.objects.get(pk=bill_id, is_soft_deleted=False)
        except (RecurringBill.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Bill not found'}, status=404)

        # Find payment for this billing period month (period_start)
        payment = BillPayment.objects.filter(
            bill=bill,
            period_start__year=year,
            period_start__month=month
        ).first()

        if payment:
            data = {
                'bill_name': bill.name,
                'status': payment.status,
                'amount': str(payment.amount) if payment.amount else '0',
                'period_start': payment.period_start.strftime('%d %b %Y') if payment.period_start else '-',
                'period_end': payment.period_end.strftime('%d %b %Y') if payment.period_end else '-',
                'due_date': payment.due_date.strftime('%d %b %Y') if payment.due_date else '-',
                'paid_date': payment.paid_date.strftime('%d %b %Y') if payment.paid_date else None,
                'payment_type': payment.get_payment_type_display() if payment.payment_type else None,
            }

            # Check if overdue
            if payment.status == 'pending' and payment.due_date and payment.due_date < date.today():
                data['status'] = 'overdue'

            return JsonResponse(data)
        else:
            # No payment record - return basic info
            return JsonResponse({
                'bill_name': bill.name,
                'status': 'no_record',
                'amount': str(bill.base_amount) if bill.base_amount else '0',
                'period_start': f'01 {month_name} {year}',
                'period_end': f'End {month_name} {year}',
                'due_date': None,
                'paid_date': None,
                'payment_type': None,
            })
    except Exception as e:
        logger.exception('Error in month_detail API')
        return JsonResponse({'error': str(e)}, status=500)


