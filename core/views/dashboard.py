"""
Dashboard view for IT FIN Track.
Only approved expenses are counted in totals and charts.
"""

import json
from datetime import datetime, timedelta, date as date_type
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.safestring import mark_safe

from core.models import Income, Expense, Category, RecurringBill, BillPayment


def _fmt(value):
    """Format a Decimal as integer string for display."""
    try:
        return '{:,.0f}'.format(value)
    except (TypeError, ValueError):
        return '0'


@login_required
def dashboard(request):
    """Main dashboard view with financial overview."""

    # Date range for current month
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)

    # Date range for current year
    first_day_of_year = today.replace(month=1, day=1)

    # Calculate totals (only APPROVED expenses count)
    total_income = Income.objects.filter(
        is_soft_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    total_expense = Expense.objects.filter(
        is_soft_deleted=False,
        status='approved'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Monthly totals (only APPROVED expenses)
    monthly_income = Income.objects.filter(
        is_soft_deleted=False,
        date__gte=first_day_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    monthly_expense = Expense.objects.filter(
        is_soft_deleted=False,
        status='approved',
        date__gte=first_day_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Calculate balance
    current_balance = total_income - total_expense

    # Pending reimbursements
    pending_reimbursements = Income.objects.filter(
        is_soft_deleted=False,
        is_reimbursable=True,
        reimbursed=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Pending approvals
    pending_approvals = Expense.objects.filter(
        is_soft_deleted=False,
        status='pending'
    ).count()

    # ── Recurring Bills Summary ──────────────────────────
    active_bills = RecurringBill.objects.filter(
        is_soft_deleted=False, is_active=True
    ).select_related('category', 'vendor').prefetch_related('payments')

    current_month = today.month
    current_year = today.year

    bills_paid_count = 0
    bills_pending_count = 0
    bills_overdue_count = 0
    bills_paid_amount = Decimal('0')
    bills_pending_amount = Decimal('0')

    bill_status_list = []

    for bill in active_bills:
        # 1) Any overdue pending payment (any month)
        overdue_pay = bill.payments.filter(
            status='pending',
            due_date__lt=today,
        ).order_by('due_date').first()

        # 2) Paid this month
        paid = bill.payments.filter(
            period_start__year=current_year,
            period_start__month=current_month,
            status='paid',
        ).first()

        # 3) Pending this month
        pending = bill.payments.filter(
            period_start__year=current_year,
            period_start__month=current_month,
            status='pending',
        ).first()

        if overdue_pay:
            bills_overdue_count += 1
            bills_pending_amount += overdue_pay.amount
            bill_status_list.append({
                'bill': bill,
                'status': 'overdue',
                'status_label': 'Overdue',
                'status_class': 'bg-danger',
                'amount': overdue_pay.amount,
                'due_date': overdue_pay.due_date,
                'paid_date': None,
            })
        elif paid:
            bills_paid_count += 1
            bills_paid_amount += paid.amount
            bill_status_list.append({
                'bill': bill,
                'status': 'paid',
                'status_label': 'Paid',
                'status_class': 'bg-success',
                'amount': paid.amount,
                'due_date': None,
                'paid_date': paid.paid_date,
            })
        elif pending:
            bills_pending_count += 1
            bills_pending_amount += pending.amount
            bill_status_list.append({
                'bill': bill,
                'status': 'pending',
                'status_label': 'Pending',
                'status_class': 'bg-warning text-dark',
                'amount': pending.amount,
                'due_date': pending.due_date,
                'paid_date': None,
            })
        else:
            bills_pending_count += 1
            bills_pending_amount += bill.base_amount
            bill_status_list.append({
                'bill': bill,
                'status': 'no_record',
                'status_label': 'No Record',
                'status_class': 'bg-secondary',
                'amount': bill.base_amount,
                'due_date': None,
                'paid_date': None,
            })

    # Sort: overdue first, then pending, then paid
    sort_map = {'overdue': 0, 'pending': 1, 'no_record': 2, 'paid': 3}
    bill_status_list.sort(key=lambda x: sort_map.get(x['status'], 9))

    total_active_bills = active_bills.count()

    # ── Category breakdown (only APPROVED expenses) ──────
    cat_breakdown = Expense.objects.filter(
        is_soft_deleted=False,
        status='approved',
        date__gte=first_day_of_year
    ).values(
        'category__name', 'category__color'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')[:8]

    # Monthly trend (last 6 months)
    six_months_ago = today - timedelta(days=180)

    inc_trend = Income.objects.filter(
        is_soft_deleted=False,
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')

    exp_trend = Expense.objects.filter(
        is_soft_deleted=False,
        status='approved',
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')

    # Recent transactions
    recent_incomes = Income.objects.filter(
        is_soft_deleted=False
    ).select_related(
        'source', 'created_by'
    ).order_by('-date', '-created_at')[:5]

    recent_expenses = Expense.objects.filter(
        is_soft_deleted=False
    ).select_related(
        'category', 'vendor', 'created_by'
    ).order_by('-date', '-created_at')[:5]

    # Prepare chart data
    trend_labels = []
    trend_inc = []
    trend_exp = []

    inc_map = {i['month']: float(i['total']) for i in inc_trend}
    exp_map = {e['month']: float(e['total']) for e in exp_trend}

    for i in range(5, -1, -1):
        md = (today - timedelta(days=i * 30)).replace(day=1)
        trend_labels.append(md.strftime('%b %Y'))
        iv = 0
        ev = 0
        for k, v in inc_map.items():
            if k.year == md.year and k.month == md.month:
                iv = v
                break
        for k, v in exp_map.items():
            if k.year == md.year and k.month == md.month:
                ev = v
                break
        trend_inc.append(iv)
        trend_exp.append(ev)

    cat_labels = [c['category__name'] or 'N/A' for c in cat_breakdown]
    cat_data = [float(c['total']) for c in cat_breakdown]
    cat_colors = [c['category__color'] or '#FF6B01' for c in cat_breakdown]

    context = {
        # Pre-formatted display strings
        'fmt_total_inc': _fmt(total_income),
        'fmt_total_exp': _fmt(total_expense),
        'fmt_balance': _fmt(current_balance),
        'fmt_mo_inc': _fmt(monthly_income),
        'fmt_mo_exp': _fmt(monthly_expense),
        'fmt_reimb': _fmt(pending_reimbursements),
        'fmt_paid_amt': _fmt(bills_paid_amount),
        'fmt_pend_amt': _fmt(bills_pending_amount),
        # Raw values for logic
        'current_balance': current_balance,
        'pending_approvals': pending_approvals,
        'recent_incomes': recent_incomes,
        'recent_expenses': recent_expenses,
        # Chart data (pre-serialized, marked safe)
        'chart_labels': mark_safe(json.dumps(trend_labels)),
        'chart_inc': mark_safe(json.dumps(trend_inc)),
        'chart_exp': mark_safe(json.dumps(trend_exp)),
        'chart_cat_lbl': mark_safe(json.dumps(cat_labels)),
        'chart_cat_dat': mark_safe(json.dumps(cat_data)),
        'chart_cat_col': mark_safe(json.dumps(cat_colors)),
        # Recurring bills
        'total_active_bills': total_active_bills,
        'bills_paid_count': bills_paid_count,
        'bills_pending_count': bills_pending_count,
        'bills_overdue_count': bills_overdue_count,
        'bill_status_list': bill_status_list,
        'month_name': today.strftime('%B %Y'),
    }

    return render(request, 'core/dashboard.html', context)
