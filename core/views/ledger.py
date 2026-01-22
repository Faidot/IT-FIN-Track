"""
Ledger views for IT FIN Track.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from core.models import Ledger, LedgerEntry
from core.forms import LedgerForm, LedgerEntryForm


@login_required
def ledger_list(request):
    """List all ledgers for the current user."""
    if request.user.is_admin:
        ledgers = Ledger.objects.filter(is_soft_deleted=False)
    else:
        ledgers = Ledger.objects.filter(is_soft_deleted=False, owner=request.user)
    
    return render(request, 'core/ledger/list.html', {'ledgers': ledgers})


@login_required
def ledger_create(request):
    """Create a new ledger."""
    if request.method == 'POST':
        form = LedgerForm(request.POST)
        if form.is_valid():
            ledger = form.save(commit=False)
            ledger.owner = request.user
            ledger.save()
            messages.success(request, 'Ledger created successfully!')
            return redirect('core:ledger_list')
    else:
        form = LedgerForm()
    
    return render(request, 'core/ledger/form.html', {
        'form': form,
        'title': 'Create Ledger',
        'action': 'Create',
    })


@login_required
def ledger_detail(request, pk):
    """View ledger details with entries."""
    ledger = get_object_or_404(Ledger, pk=pk, is_soft_deleted=False)
    
    # Check permission
    if not request.user.is_admin and ledger.owner != request.user:
        messages.error(request, 'You do not have permission to view this ledger.')
        return redirect('core:ledger_list')
    
    entries = ledger.entries.filter(is_soft_deleted=False).order_by('-date', '-created_at')
    
    # Pagination
    paginator = Paginator(entries, 20)
    page = request.GET.get('page', 1)
    entries = paginator.get_page(page)
    
    return render(request, 'core/ledger/detail.html', {
        'ledger': ledger,
        'entries': entries,
    })


@login_required
def ledger_entry_create(request, ledger_pk):
    """Create a new ledger entry."""
    ledger = get_object_or_404(Ledger, pk=ledger_pk, is_soft_deleted=False)
    
    # Check permission
    if not request.user.is_admin and ledger.owner != request.user:
        messages.error(request, 'You do not have permission to add entries to this ledger.')
        return redirect('core:ledger_list')
    
    if request.method == 'POST':
        form = LedgerEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.ledger = ledger
            entry.created_by = request.user
            entry.save()
            messages.success(request, 'Entry added successfully!')
            return redirect('core:ledger_detail', pk=ledger_pk)
    else:
        form = LedgerEntryForm(initial={'ledger': ledger})
    
    return render(request, 'core/ledger/entry_form.html', {
        'form': form,
        'ledger': ledger,
        'title': 'Add Entry',
        'action': 'Create',
    })


@login_required
def ledger_delete(request, pk):
    """Soft delete a ledger."""
    ledger = get_object_or_404(Ledger, pk=pk, is_soft_deleted=False)
    
    if not request.user.is_admin and ledger.owner != request.user:
        messages.error(request, 'You do not have permission to delete this ledger.')
        return redirect('core:ledger_list')
    
    if request.method == 'POST':
        ledger.is_soft_deleted = True
        ledger.save()
        messages.success(request, 'Ledger deleted successfully!')
        return redirect('core:ledger_list')
    
    return render(request, 'core/ledger/confirm_delete.html', {'ledger': ledger})
