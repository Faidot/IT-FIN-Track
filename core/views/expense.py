"""
Expense views for IT FIN Track.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from core.models import Expense, ExpenseBill, Category, Vendor, Income
from core.forms.expense import ExpenseForm, ExpenseWithBillsForm


@login_required
def expense_list(request):
    """List all expenses with filtering and pagination."""
    expenses = Expense.objects.filter(
        is_soft_deleted=False
    ).select_related('category', 'vendor', 'created_by', 'linked_income')
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        expenses = expenses.filter(
            Q(description__icontains=search) |
            Q(purpose__icontains=search) |
            Q(invoice_number__icontains=search) |
            Q(vendor__name__icontains=search)
        )
    
    # Filter by category
    category = request.GET.get('category', '')
    if category:
        expenses = expenses.filter(category_id=category)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        expenses = expenses.filter(status=status)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)
    
    # Ordering
    order = request.GET.get('order', '-date')
    expenses = expenses.order_by(order, '-created_at')
    
    # Pagination
    paginator = Paginator(expenses, 20)
    page = request.GET.get('page', 1)
    expenses = paginator.get_page(page)
    
    categories = Category.objects.filter(is_soft_deleted=False, is_active=True)
    
    context = {
        'expenses': expenses,
        'categories': categories,
        'statuses': Expense.Status.choices,
        'search': search,
        'category_filter': category,
        'status_filter': status,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'core/expense/list.html', context)


@login_required
def expense_create(request):
    """Create a new expense record with bill uploads."""
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to create expense records.')
        return redirect('core:expense_list')
    
    if request.method == 'POST':
        form = ExpenseWithBillsForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            
            # Handle multiple bill uploads
            files = request.FILES.getlist('bills')
            for f in files:
                ExpenseBill.objects.create(
                    expense=expense,
                    file=f,
                    original_filename=f.name,
                    uploaded_by=request.user
                )
            
            messages.success(request, 'Expense record created successfully!')
            return redirect('core:expense_list')
    else:
        form = ExpenseWithBillsForm()
    
    # Get available data for dropdowns
    categories = Category.objects.filter(is_soft_deleted=False, is_active=True)
    vendors = Vendor.objects.filter(is_soft_deleted=False, is_active=True)
    incomes = Income.objects.filter(is_soft_deleted=False).order_by('-date')[:50]
    
    return render(request, 'core/expense/form.html', {
        'form': form,
        'categories': categories,
        'vendors': vendors,
        'incomes': incomes,
        'title': 'Add Expense',
        'action': 'Create',
    })


@login_required
def expense_edit(request, pk):
    """Edit an existing expense record."""
    expense = get_object_or_404(Expense, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to edit expense records.')
        return redirect('core:expense_list')
    
    if request.method == 'POST':
        form = ExpenseWithBillsForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            
            # Handle new bill uploads
            files = request.FILES.getlist('bills')
            for f in files:
                ExpenseBill.objects.create(
                    expense=expense,
                    file=f,
                    original_filename=f.name,
                    uploaded_by=request.user
                )
            
            messages.success(request, 'Expense record updated successfully!')
            return redirect('core:expense_list')
    else:
        form = ExpenseWithBillsForm(instance=expense)
    
    categories = Category.objects.filter(is_soft_deleted=False, is_active=True)
    vendors = Vendor.objects.filter(is_soft_deleted=False, is_active=True)
    incomes = Income.objects.filter(is_soft_deleted=False).order_by('-date')[:50]
    
    return render(request, 'core/expense/form.html', {
        'form': form,
        'expense': expense,
        'categories': categories,
        'vendors': vendors,
        'incomes': incomes,
        'title': 'Edit Expense',
        'action': 'Update',
    })


@login_required
def expense_detail(request, pk):
    """View expense details with bills."""
    expense = get_object_or_404(
        Expense.objects.select_related('category', 'vendor', 'created_by', 'linked_income', 'approved_by'),
        pk=pk,
        is_soft_deleted=False
    )
    bills = expense.bills.all()
    return render(request, 'core/expense/detail.html', {
        'expense': expense,
        'bills': bills,
    })


@login_required
def expense_delete(request, pk):
    """Soft delete an expense record."""
    expense = get_object_or_404(Expense, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_delete:
        messages.error(request, 'You do not have permission to delete expense records.')
        return redirect('core:expense_list')
    
    if request.method == 'POST':
        expense.is_soft_deleted = True
        expense.save()
        messages.success(request, 'Expense record deleted successfully!')
        return redirect('core:expense_list')
    
    return render(request, 'core/expense/confirm_delete.html', {'expense': expense})


@login_required
def expense_approve(request, pk):
    """Approve an expense."""
    expense = get_object_or_404(Expense, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_approve:
        messages.error(request, 'You do not have permission to approve expenses.')
        return redirect('core:expense_detail', pk=pk)
    
    if request.method == 'POST':
        expense.status = Expense.Status.APPROVED
        expense.approved_by = request.user
        expense.approved_date = timezone.now()
        expense.save()
        messages.success(request, 'Expense approved successfully!')
    
    return redirect('core:expense_detail', pk=pk)


@login_required
def expense_reject(request, pk):
    """Reject an expense."""
    expense = get_object_or_404(Expense, pk=pk, is_soft_deleted=False)
    
    if not request.user.can_approve:
        messages.error(request, 'You do not have permission to reject expenses.')
        return redirect('core:expense_detail', pk=pk)
    
    if request.method == 'POST':
        expense.status = Expense.Status.REJECTED
        expense.approved_by = request.user
        expense.approved_date = timezone.now()
        expense.rejection_reason = request.POST.get('reason', '')
        expense.save()
        messages.success(request, 'Expense rejected.')
    
    return redirect('core:expense_detail', pk=pk)


@login_required
def bill_delete(request, pk):
    """Delete a bill attachment."""
    bill = get_object_or_404(ExpenseBill, pk=pk)
    expense_pk = bill.expense.pk
    
    if not request.user.can_edit:
        messages.error(request, 'You do not have permission to delete bills.')
        return redirect('core:expense_detail', pk=expense_pk)
    
    if request.method == 'POST':
        bill.file.delete()
        bill.delete()
        messages.success(request, 'Bill deleted successfully!')
    
    return redirect('core:expense_detail', pk=expense_pk)
