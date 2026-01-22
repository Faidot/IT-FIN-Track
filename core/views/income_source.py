"""
Income Source views for IT FIN Track.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from core.models import IncomeSource
from core.forms import IncomeSourceForm


@login_required
def income_source_list(request):
    """List all income sources."""
    sources = IncomeSource.objects.filter(is_soft_deleted=False).order_by('name')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        sources = sources.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(contact_person__icontains=search)
        )
    
    context = {
        'sources': sources,
        'search': search,
    }
    return render(request, 'core/income_source/list.html', context)


@login_required
def income_source_create(request):
    """Create a new income source."""
    if not request.user.is_admin:
        messages.error(request, 'Only admins can add income sources.')
        return redirect('core:income_source_list')
    
    if request.method == 'POST':
        form = IncomeSourceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income source created successfully!')
            return redirect('core:income_source_list')
    else:
        form = IncomeSourceForm()
    
    context = {
        'form': form,
        'title': 'Add Income Source',
        'action': 'Save',
    }
    return render(request, 'core/income_source/form.html', context)


@login_required
def income_source_edit(request, pk):
    """Edit an income source."""
    source = get_object_or_404(IncomeSource, pk=pk, is_soft_deleted=False)
    
    if not request.user.is_admin:
        messages.error(request, 'Only admins can edit income sources.')
        return redirect('core:income_source_list')
    
    if request.method == 'POST':
        form = IncomeSourceForm(request.POST, instance=source)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income source updated successfully!')
            return redirect('core:income_source_list')
    else:
        form = IncomeSourceForm(instance=source)
    
    context = {
        'form': form,
        'source': source,
        'title': 'Edit Income Source',
        'action': 'Update',
    }
    return render(request, 'core/income_source/form.html', context)


@login_required
def income_source_detail(request, pk):
    """View income source details with transaction history."""
    source = get_object_or_404(IncomeSource, pk=pk, is_soft_deleted=False)
    incomes = source.incomes.filter(is_soft_deleted=False).order_by('-date')[:20]
    
    context = {
        'source': source,
        'incomes': incomes,
    }
    return render(request, 'core/income_source/detail.html', context)


@login_required
def income_source_delete(request, pk):
    """Soft delete an income source."""
    source = get_object_or_404(IncomeSource, pk=pk, is_soft_deleted=False)
    
    if not request.user.is_admin:
        messages.error(request, 'Only admins can delete income sources.')
        return redirect('core:income_source_list')
    
    if request.method == 'POST':
        source.is_soft_deleted = True
        source.save()
        messages.success(request, 'Income source deleted successfully!')
        return redirect('core:income_source_list')
    
    context = {
        'source': source,
    }
    return render(request, 'core/income_source/confirm_delete.html', context)
