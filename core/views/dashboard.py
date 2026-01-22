"""
Dashboard view for IT FIN Track.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from core.models import Income, Expense, Category


@login_required
def dashboard(request):
    """Main dashboard view with financial overview."""
    
    # Date range for current month
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    
    # Date range for current year
    first_day_of_year = today.replace(month=1, day=1)
    
    # Calculate totals
    total_income = Income.objects.filter(
        is_soft_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_expense = Expense.objects.filter(
        is_soft_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Monthly totals
    monthly_income = Income.objects.filter(
        is_soft_deleted=False,
        date__gte=first_day_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    monthly_expense = Expense.objects.filter(
        is_soft_deleted=False,
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
    
    # Category breakdown for chart
    category_breakdown = Expense.objects.filter(
        is_soft_deleted=False,
        date__gte=first_day_of_year
    ).values(
        'category__name', 'category__color'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')[:8]
    
    # Monthly trend for chart (last 6 months)
    six_months_ago = today - timedelta(days=180)
    
    monthly_income_trend = Income.objects.filter(
        is_soft_deleted=False,
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    monthly_expense_trend = Expense.objects.filter(
        is_soft_deleted=False,
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Recent transactions
    recent_incomes = Income.objects.filter(
        is_soft_deleted=False
    ).select_related('source', 'created_by').order_by('-date', '-created_at')[:5]
    
    recent_expenses = Expense.objects.filter(
        is_soft_deleted=False
    ).select_related('category', 'vendor', 'created_by').order_by('-date', '-created_at')[:5]
    
    # Prepare chart data
    income_trend_labels = []
    income_trend_data = []
    expense_trend_data = []
    
    # Create a dictionary for easy lookup
    income_by_month = {item['month']: float(item['total']) for item in monthly_income_trend}
    expense_by_month = {item['month']: float(item['total']) for item in monthly_expense_trend}
    
    # Generate last 6 months
    for i in range(5, -1, -1):
        month_date = (today - timedelta(days=i*30)).replace(day=1)
        month_key = month_date.replace(day=1)
        income_trend_labels.append(month_date.strftime('%b %Y'))
        
        # Find matching data
        income_total = 0
        expense_total = 0
        for key, val in income_by_month.items():
            if key.year == month_date.year and key.month == month_date.month:
                income_total = val
                break
        for key, val in expense_by_month.items():
            if key.year == month_date.year and key.month == month_date.month:
                expense_total = val
                break
        
        income_trend_data.append(income_total)
        expense_trend_data.append(expense_total)
    
    # Category chart data
    category_labels = [item['category__name'] or 'Uncategorized' for item in category_breakdown]
    category_data = [float(item['total']) for item in category_breakdown]
    category_colors = [item['category__color'] or '#FF6B01' for item in category_breakdown]
    
    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'current_balance': current_balance,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'pending_reimbursements': pending_reimbursements,
        'pending_approvals': pending_approvals,
        'recent_incomes': recent_incomes,
        'recent_expenses': recent_expenses,
        'income_trend_labels': income_trend_labels,
        'income_trend_data': income_trend_data,
        'expense_trend_data': expense_trend_data,
        'category_labels': category_labels,
        'category_data': category_data,
        'category_colors': category_colors,
    }
    
    return render(request, 'core/dashboard.html', context)
