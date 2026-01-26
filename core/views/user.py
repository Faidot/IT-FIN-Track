"""
User management views for IT FIN Track.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count

from core.models import User
from core.forms.user import UserCreateForm, UserEditForm, PasswordResetForm


def admin_required(view_func):
    """Decorator to check if user is admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, 'Only admins can access user management.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def user_list(request):
    """List all users with search and filter."""
    users = User.objects.filter(is_soft_deleted=False).annotate(
        income_count=Count('incomes_created', distinct=True),
        expense_count=Count('expenses_created', distinct=True),
    )
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Filter by role
    role = request.GET.get('role', '')
    if role:
        users = users.filter(role=role)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    
    # Ordering
    users = users.order_by('first_name', 'last_name')
    
    # Pagination
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'search': search,
        'role_filter': role,
        'status_filter': status,
        'roles': User.Role.choices,
    }
    
    return render(request, 'core/user/list.html', context)


@login_required
@admin_required
def user_create(request):
    """Create a new user."""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.get_full_name()}" created successfully!')
            return redirect('core:user_list')
    else:
        form = UserCreateForm()
    
    return render(request, 'core/user/form.html', {
        'form': form,
        'title': 'Add New User',
        'action': 'Create',
    })


@login_required
@admin_required
def user_edit(request, pk):
    """Edit an existing user."""
    user = get_object_or_404(User, pk=pk, is_soft_deleted=False)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.get_full_name()}" updated successfully!')
            return redirect('core:user_list')
    else:
        form = UserEditForm(instance=user)
    
    return render(request, 'core/user/form.html', {
        'form': form,
        'user_obj': user,
        'title': f'Edit User: {user.get_full_name()}',
        'action': 'Update',
    })


@login_required
@admin_required
def user_detail(request, pk):
    """View user details."""
    user = get_object_or_404(User, pk=pk, is_soft_deleted=False)
    
    # Get recent activity
    recent_incomes = user.incomes_created.filter(is_soft_deleted=False).order_by('-created_at')[:5]
    recent_expenses = user.expenses_created.filter(is_soft_deleted=False).order_by('-created_at')[:5]
    
    context = {
        'user_obj': user,
        'recent_incomes': recent_incomes,
        'recent_expenses': recent_expenses,
    }
    
    return render(request, 'core/user/detail.html', context)


@login_required
@admin_required
def user_reset_password(request, pk):
    """Reset user password."""
    user = get_object_or_404(User, pk=pk, is_soft_deleted=False)
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            messages.success(request, f'Password for "{user.get_full_name()}" has been reset.')
            return redirect('core:user_list')
    else:
        form = PasswordResetForm()
    
    return render(request, 'core/user/reset_password.html', {
        'form': form,
        'user_obj': user,
    })


@login_required
@admin_required
def user_toggle_status(request, pk):
    """Toggle user active status."""
    user = get_object_or_404(User, pk=pk, is_soft_deleted=False)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User "{user.get_full_name()}" has been {status}.')
    
    return redirect('core:user_list')
