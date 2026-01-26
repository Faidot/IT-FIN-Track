"""
Payment Tracker views for IT FIN Track.
A unified view of all financial transactions with filters.
Shows income and linked expenses together when filtering by source.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from decimal import Decimal
from itertools import chain
from operator import attrgetter

from core.models import Income, Expense, Vendor, Category, IncomeSource, User


@login_required
def payment_tracker(request):
    """Unified payment tracker showing all income and expenses."""
    
    # Get filter parameters
    filter_type = request.GET.get('type', 'all')  # all, income, expense
    vendor_id = request.GET.get('vendor', '')
    category_id = request.GET.get('category', '')
    source_id = request.GET.get('source', '')
    user_id = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Start with base querysets (only approved expenses count)
    incomes = Income.objects.filter(is_soft_deleted=False).select_related('source', 'created_by')
    expenses = Expense.objects.filter(is_soft_deleted=False, status='approved').select_related('vendor', 'category', 'created_by', 'linked_income')
    
    # If filtering by income source, show income from that source AND expenses linked to those incomes
    if source_id:
        incomes = incomes.filter(source_id=source_id)
        # Get all income IDs from this source
        income_ids = list(incomes.values_list('id', flat=True))
        # Filter expenses that are linked to these incomes OR have no linked income but we still want to show unlinked
        expenses = expenses.filter(linked_income_id__in=income_ids)
    
    if vendor_id:
        expenses = expenses.filter(vendor_id=vendor_id)
    
    if category_id:
        expenses = expenses.filter(category_id=category_id)
    
    if user_id:
        incomes = incomes.filter(created_by_id=user_id)
        expenses = expenses.filter(created_by_id=user_id)
    
    if date_from:
        incomes = incomes.filter(date__gte=date_from)
        expenses = expenses.filter(date__gte=date_from)
    
    if date_to:
        incomes = incomes.filter(date__lte=date_to)
        expenses = expenses.filter(date__lte=date_to)
    
    if search:
        incomes = incomes.filter(
            Q(description__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(source_detail__icontains=search)
        )
        expenses = expenses.filter(
            Q(description__icontains=search) |
            Q(purpose__icontains=search) |
            Q(invoice_number__icontains=search)
        )
    
    # Calculate totals
    total_income = incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    balance = total_income - total_expense
    
    # Prepare transactions with type indicator
    income_list = []
    expense_list = []
    
    if filter_type in ['all', 'income']:
        for income in incomes:
            income.transaction_type = 'income'
            income.display_source = income.source.name if income.source else 'Unknown'
            income.linked_info = f"{income.linked_expenses.filter(is_soft_deleted=False, status='approved').count()} expenses linked"
            income_list.append(income)
    
    if filter_type in ['all', 'expense']:
        for expense in expenses:
            expense.transaction_type = 'expense'
            expense.display_source = f"{expense.category.name if expense.category else 'Unknown'}"
            if expense.linked_income:
                expense.linked_info = f"From: {expense.linked_income.source.name}"
            else:
                expense.linked_info = ""
            expense_list.append(expense)
    
    # Combine and sort by date (newest first)
    transactions = sorted(
        chain(income_list, expense_list),
        key=attrgetter('date'),
        reverse=True
    )
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page = request.GET.get('page', 1)
    transactions = paginator.get_page(page)
    
    # Get filter options
    vendors = Vendor.objects.filter(is_soft_deleted=False, is_active=True).order_by('name')
    categories = Category.objects.filter(is_soft_deleted=False, is_active=True).order_by('name')
    sources = IncomeSource.objects.filter(is_soft_deleted=False, is_active=True).order_by('name')
    users = User.objects.filter(is_soft_deleted=False, is_active=True).order_by('first_name')
    
    context = {
        'transactions': transactions,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        # Filters
        'vendors': vendors,
        'categories': categories,
        'sources': sources,
        'users': users,
        # Current filter values
        'filter_type': filter_type,
        'vendor_id': vendor_id,
        'category_id': category_id,
        'source_id': source_id,
        'user_id': user_id,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    }
    
    return render(request, 'core/payment_tracker/list.html', context)
