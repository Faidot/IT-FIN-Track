"""
Category views for IT FIN Track.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q

from core.models import Category
from core.forms import CategoryForm


@login_required
def category_list(request):
    """List all categories with expense totals."""
    # Filter out soft-deleted expenses in the aggregation
    categories = Category.objects.filter(is_soft_deleted=False).annotate(
        total_expense=Sum('expenses__amount', filter=Q(expenses__is_soft_deleted=False), default=0),
        count_expense=Count('expenses', filter=Q(expenses__is_soft_deleted=False))
    ).order_by('name')
    
    return render(request, 'core/category/list.html', {'categories': categories})


@login_required
def category_create(request):
    """Create a new category."""
    if not request.user.is_admin:
        messages.error(request, 'Only admins can create categories.')
        return redirect('core:category_list')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('core:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'core/category/form.html', {
        'form': form,
        'title': 'Add Category',
        'action': 'Create',
    })


@login_required
def category_edit(request, pk):
    """Edit an existing category."""
    category = get_object_or_404(Category, pk=pk, is_soft_deleted=False)
    
    if not request.user.is_admin:
        messages.error(request, 'Only admins can edit categories.')
        return redirect('core:category_list')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('core:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'core/category/form.html', {
        'form': form,
        'category': category,
        'title': 'Edit Category',
        'action': 'Update',
    })


@login_required
def category_delete(request, pk):
    """Soft delete a category."""
    category = get_object_or_404(Category, pk=pk, is_soft_deleted=False)
    
    if not request.user.is_admin:
        messages.error(request, 'Only admins can delete categories.')
        return redirect('core:category_list')
    
    if request.method == 'POST':
        category.is_soft_deleted = True
        category.save()
        messages.success(request, 'Category deleted successfully!')
        return redirect('core:category_list')
    
    return render(request, 'core/category/confirm_delete.html', {'category': category})
