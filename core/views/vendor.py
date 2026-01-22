"""
Vendor views for IT FIN Track.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count

from core.models import Vendor
from core.forms import VendorForm


@login_required
def vendor_list(request):
    """List all vendors with search and pagination."""
    # Filter out soft-deleted expenses in the aggregation
    vendors = Vendor.objects.filter(is_soft_deleted=False).annotate(
        total_expense=Sum('expenses__amount', filter=Q(expenses__is_soft_deleted=False), default=0),
        count_expense=Count('expenses', filter=Q(expenses__is_soft_deleted=False))
    )
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        vendors = vendors.filter(
            Q(name__icontains=search) |
            Q(contact_person__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Ordering
    order = request.GET.get('order', 'name')
    vendors = vendors.order_by(order)
    
    # Pagination
    paginator = Paginator(vendors, 20)
    page = request.GET.get('page', 1)
    vendors = paginator.get_page(page)
    
    return render(request, 'core/vendor/list.html', {
        'vendors': vendors,
        'search': search,
    })


@login_required
def vendor_create(request):
    """Create a new vendor."""
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to create vendors.')
        return redirect('core:vendor_list')
    
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor created successfully!')
            return redirect('core:vendor_list')
    else:
        form = VendorForm()
    
    return render(request, 'core/vendor/form.html', {
        'form': form,
        'title': 'Add Vendor',
        'action': 'Create',
    })


@login_required
def vendor_edit(request, pk):
    """Edit an existing vendor."""
    vendor = get_object_or_404(Vendor, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to edit vendors.')
        return redirect('core:vendor_list')
    
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor updated successfully!')
            return redirect('core:vendor_list')
    else:
        form = VendorForm(instance=vendor)
    
    return render(request, 'core/vendor/form.html', {
        'form': form,
        'vendor': vendor,
        'title': 'Edit Vendor',
        'action': 'Update',
    })


@login_required
def vendor_detail(request, pk):
    """View vendor details with transaction history."""
    vendor = get_object_or_404(Vendor, pk=pk, is_soft_deleted=False)
    expenses = vendor.expenses.filter(is_soft_deleted=False).order_by('-date')[:20]
    
    return render(request, 'core/vendor/detail.html', {
        'vendor': vendor,
        'expenses': expenses,
    })


@login_required
def vendor_delete(request, pk):
    """Soft delete a vendor."""
    vendor = get_object_or_404(Vendor, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_delete:
        messages.error(request, 'You do not have permission to delete vendors.')
        return redirect('core:vendor_list')
    
    if request.method == 'POST':
        vendor.is_soft_deleted = True
        vendor.save()
        messages.success(request, 'Vendor deleted successfully!')
        return redirect('core:vendor_list')
    
    return render(request, 'core/vendor/confirm_delete.html', {'vendor': vendor})
