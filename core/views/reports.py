"""
Reports and Audit Trail views for IT FIN Track.
"""

import io
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator

from core.models import Income, Expense, AuditLog, Category, Vendor


@login_required
def report_dashboard(request):
    """Reports dashboard overview."""
    return render(request, 'core/reports/dashboard.html')


@login_required
def monthly_expense_report(request):
    """Monthly IT expense report."""
    # Get date parameters
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Date range for the month
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    start_date = datetime(year, month, 1).date()
    
    # Get expenses
    expenses = Expense.objects.filter(
        is_soft_deleted=False,
        date__gte=start_date,
        date__lt=end_date
    ).select_related('category', 'vendor', 'created_by')
    
    # Summary
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Category breakdown
    category_breakdown = expenses.values(
        'category__name', 'category__color'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Vendor breakdown
    vendor_breakdown = expenses.exclude(vendor__isnull=True).values(
        'vendor__name'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')[:10]
    
    context = {
        'year': year,
        'month': month,
        'month_name': datetime(year, month, 1).strftime('%B'),
        'start_date': start_date,
        'end_date': end_date - timedelta(days=1),
        'expenses': expenses,
        'total_expense': total_expense,
        'category_breakdown': category_breakdown,
        'vendor_breakdown': vendor_breakdown,
        'years': range(2020, timezone.now().year + 1),
        'months': range(1, 13),
    }
    
    return render(request, 'core/reports/monthly_expense.html', context)


@login_required
def income_expense_statement(request):
    """Income vs Expense statement."""
    # Get date parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = timezone.now().strftime('%Y-%m-%d')
    
    # Get data
    incomes = Income.objects.filter(
        is_soft_deleted=False,
        date__gte=date_from,
        date__lte=date_to
    ).order_by('-date')
    
    expenses = Expense.objects.filter(
        is_soft_deleted=False,
        date__gte=date_from,
        date__lte=date_to
    ).select_related('category').order_by('-date')
    
    # Summary
    total_income = incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    net_balance = total_income - total_expense
    
    # Income by source
    income_by_source = incomes.values('source').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'incomes': incomes,
        'expenses': expenses,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'income_by_source': income_by_source,
    }
    
    return render(request, 'core/reports/income_expense.html', context)


@login_required
def reimbursement_report(request):
    """Pending reimbursement report."""
    # Get pending reimbursements
    pending = Income.objects.filter(
        is_soft_deleted=False,
        is_reimbursable=True,
        reimbursed=False
    ).order_by('-date')
    
    # Get completed reimbursements
    completed = Income.objects.filter(
        is_soft_deleted=False,
        is_reimbursable=True,
        reimbursed=True
    ).order_by('-reimbursed_date')[:20]
    
    # Summary
    total_pending = pending.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_completed = completed.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    context = {
        'pending': pending,
        'completed': completed,
        'total_pending': total_pending,
        'total_completed': total_completed,
    }
    
    return render(request, 'core/reports/reimbursement.html', context)


@login_required
def audit_trail(request):
    """Audit trail report."""
    logs = AuditLog.objects.select_related('user').all()
    
    # Filter by user
    user_id = request.GET.get('user', '')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Filter by action
    action = request.GET.get('action', '')
    if action:
        logs = logs.filter(action=action)
    
    # Filter by model
    model = request.GET.get('model', '')
    if model:
        logs = logs.filter(model_name=model)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        logs = logs.filter(changes_summary__icontains=search)
    
    # Pagination
    paginator = Paginator(logs.order_by('-timestamp'), 50)
    page = request.GET.get('page', 1)
    logs = paginator.get_page(page)
    
    # Get filter options
    from core.models import User
    users = User.objects.filter(is_soft_deleted=False)
    actions = AuditLog.ActionType.choices
    models = AuditLog.objects.values_list('model_name', flat=True).distinct()
    
    context = {
        'logs': logs,
        'users': users,
        'actions': actions,
        'models': models,
        'user_filter': user_id,
        'action_filter': action,
        'model_filter': model,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    }
    
    return render(request, 'core/reports/audit_trail.html', context)


@login_required
def export_excel(request, report_type):
    """Export report to Excel."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
    except ImportError:
        return HttpResponse('openpyxl not installed', status=500)
    
    wb = Workbook()
    ws = wb.active
    
    # Header style
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4E4E4E', end_color='4E4E4E', fill_type='solid')
    
    if report_type == 'expenses':
        ws.title = 'Expenses'
        headers = ['Date', 'Category', 'Vendor', 'Amount', 'Description', 'Status', 'Created By']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        expenses = Expense.objects.filter(is_soft_deleted=False).select_related(
            'category', 'vendor', 'created_by'
        ).order_by('-date')
        
        for row, expense in enumerate(expenses, 2):
            ws.cell(row=row, column=1, value=expense.date.strftime('%Y-%m-%d'))
            ws.cell(row=row, column=2, value=expense.category.name if expense.category else '')
            ws.cell(row=row, column=3, value=expense.vendor.name if expense.vendor else '')
            ws.cell(row=row, column=4, value=float(expense.amount))
            ws.cell(row=row, column=5, value=expense.description)
            ws.cell(row=row, column=6, value=expense.get_status_display())
            ws.cell(row=row, column=7, value=expense.created_by.username)
        
        filename = f'expenses_{timezone.now().strftime("%Y%m%d")}.xlsx'
    
    elif report_type == 'incomes':
        ws.title = 'Incomes'
        headers = ['Date', 'Source', 'Amount', 'Payment Mode', 'Reference', 'Description', 'Created By']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        incomes = Income.objects.filter(is_soft_deleted=False).select_related(
            'created_by'
        ).order_by('-date')
        
        for row, income in enumerate(incomes, 2):
            ws.cell(row=row, column=1, value=income.date.strftime('%Y-%m-%d'))
            ws.cell(row=row, column=2, value=income.get_source_display())
            ws.cell(row=row, column=3, value=float(income.amount))
            ws.cell(row=row, column=4, value=income.get_payment_mode_display())
            ws.cell(row=row, column=5, value=income.reference_number)
            ws.cell(row=row, column=6, value=income.description)
            ws.cell(row=row, column=7, value=income.created_by.username)
        
        filename = f'incomes_{timezone.now().strftime("%Y%m%d")}.xlsx'
    
    else:
        return HttpResponse('Invalid report type', status=400)
    
    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response
