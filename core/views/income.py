"""
Income views for IT FIN Track.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum

from core.models import Income, IncomeSource
from core.forms import IncomeForm


@login_required
def income_list(request):
    """List all income records with filtering."""
    incomes = Income.objects.filter(is_soft_deleted=False).select_related('source').order_by('-date', '-created_at')
    
    # Filtering
    search = request.GET.get('search', '')
    source_filter = request.GET.get('source', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search:
        incomes = incomes.filter(
            Q(description__icontains=search) |
            Q(source_detail__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(source__name__icontains=search)
        )
    
    if source_filter:
        incomes = incomes.filter(source_id=source_filter)
    
    if date_from:
        incomes = incomes.filter(date__gte=date_from)
    
    if date_to:
        incomes = incomes.filter(date__lte=date_to)
    
    # Calculate total of filtered results (before pagination)
    total_amount = incomes.aggregate(total=Sum('amount'))['total'] or 0
    total_count = incomes.count()
    
    # Pagination
    paginator = Paginator(incomes, 15)
    page = request.GET.get('page')
    incomes = paginator.get_page(page)
    
    # Get source choices for filter
    sources = IncomeSource.objects.filter(is_soft_deleted=False, is_active=True)
    
    context = {
        'incomes': incomes,
        'search': search,
        'source_filter': source_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sources': sources,
        'total_amount': total_amount,
        'total_count': total_count,
    }
    return render(request, 'core/income/list.html', context)


@login_required
def income_create(request):
    """Create a new income record."""
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.created_by = request.user
            income.save()
            messages.success(request, 'Income record created successfully!')
            return redirect('core:income_list')
    else:
        form = IncomeForm()
    
    context = {
        'form': form,
        'title': 'Add Income',
        'action': 'Save Income',
    }
    return render(request, 'core/income/form.html', context)


@login_required
def income_edit(request, pk):
    """Edit an existing income record."""
    income = get_object_or_404(Income, pk=pk, is_soft_deleted=False)
    
    # Check permission
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to edit records.')
        return redirect('core:income_list')
    
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income record updated successfully!')
            return redirect('core:income_detail', pk=pk)
    else:
        form = IncomeForm(instance=income)
    
    context = {
        'form': form,
        'income': income,
        'title': 'Edit Income',
        'action': 'Update Income',
    }
    return render(request, 'core/income/form.html', context)


@login_required
def income_detail(request, pk):
    """View income record details."""
    income = get_object_or_404(Income, pk=pk, is_soft_deleted=False)
    
    context = {
        'income': income,
    }
    return render(request, 'core/income/detail.html', context)


@login_required
def income_delete(request, pk):
    """Soft delete an income record."""
    income = get_object_or_404(Income, pk=pk, is_soft_deleted=False)
    
    # Check permission
    if not request.user.can_delete:
        messages.error(request, 'You do not have permission to delete records.')
        return redirect('core:income_list')
    
    if request.method == 'POST':
        income.is_soft_deleted = True
        income.save()
        messages.success(request, 'Income record deleted successfully!')
        return redirect('core:income_list')
    
    context = {
        'income': income,
    }
    return render(request, 'core/income/confirm_delete.html', context)
