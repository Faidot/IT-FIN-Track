"""
Views for Role management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.models import Role
from core.forms.role import RoleForm


def admin_required(view_func):
    """Decorator to require admin/role management access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.can_manage_roles:
            messages.error(request, 'You do not have permission to manage roles.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def role_list(request):
    """List all roles."""
    roles = Role.objects.filter(is_soft_deleted=False).order_by('name')
    
    context = {
        'roles': roles,
    }
    return render(request, 'core/roles/list.html', context)


@login_required
@admin_required
def role_create(request):
    """Create a new role."""
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Role "{role.name}" created successfully!')
            return redirect('core:role_list')
    else:
        form = RoleForm()
    
    context = {
        'form': form,
        'title': 'Create Role',
    }
    return render(request, 'core/roles/form.html', context)


@login_required
@admin_required
def role_edit(request, pk):
    """Edit an existing role."""
    role = get_object_or_404(Role, pk=pk, is_soft_deleted=False)
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, f'Role "{role.name}" updated successfully!')
            return redirect('core:role_list')
    else:
        form = RoleForm(instance=role)
    
    context = {
        'form': form,
        'role': role,
        'title': f'Edit Role: {role.name}',
    }
    return render(request, 'core/roles/form.html', context)


@login_required
@admin_required
def role_delete(request, pk):
    """Soft delete a role."""
    role = get_object_or_404(Role, pk=pk, is_soft_deleted=False)
    
    # Check if any users have this role
    user_count = role.users.filter(is_soft_deleted=False).count()
    
    if request.method == 'POST':
        if user_count > 0:
            messages.error(request, f'Cannot delete role "{role.name}" because {user_count} user(s) are assigned to it.')
            return redirect('core:role_list')
        
        role.is_soft_deleted = True
        role.save()
        messages.success(request, f'Role "{role.name}" deleted successfully!')
        return redirect('core:role_list')
    
    context = {
        'role': role,
        'user_count': user_count,
    }
    return render(request, 'core/roles/delete.html', context)


@login_required
@admin_required
def role_detail(request, pk):
    """View role details and assigned users."""
    role = get_object_or_404(Role, pk=pk, is_soft_deleted=False)
    users = role.users.filter(is_soft_deleted=False)
    
    context = {
        'role': role,
        'users': users,
    }
    return render(request, 'core/roles/detail.html', context)
