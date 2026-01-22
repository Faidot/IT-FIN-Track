"""
Authentication views for IT FIN Track.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from core.models import AuditLog


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_soft_deleted:
                messages.error(request, 'This account has been deactivated.')
            elif not user.is_active:
                messages.error(request, 'This account is inactive.')
            else:
                login(request, user)
                
                # Log the login action
                AuditLog.log_action(
                    user=user,
                    action=AuditLog.ActionType.LOGIN,
                    model_name='User',
                    object_id=user.id,
                    object_repr=str(user),
                    ip_address=getattr(request, 'client_ip', None),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_path=request.path,
                    request_method=request.method,
                )
                
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect to next URL or dashboard
                next_url = request.GET.get('next', 'core:dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/auth/login.html')


@login_required
def logout_view(request):
    """Handle user logout."""
    user = request.user
    
    # Log the logout action
    AuditLog.log_action(
        user=user,
        action=AuditLog.ActionType.LOGOUT,
        model_name='User',
        object_id=user.id,
        object_repr=str(user),
        ip_address=getattr(request, 'client_ip', None),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        request_path=request.path,
        request_method=request.method,
    )
    
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('core:login')


@login_required
def profile_view(request):
    """View and update user profile."""
    user = request.user
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.phone = request.POST.get('phone', '').strip()
        user.department = request.POST.get('department', '').strip()
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('core:profile')
    
    return render(request, 'core/auth/profile.html', {'user': user})


@login_required
@require_http_methods(["POST"])
def change_password_view(request):
    """Handle password change."""
    user = request.user
    current_password = request.POST.get('current_password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')
    
    if not user.check_password(current_password):
        messages.error(request, 'Current password is incorrect.')
    elif new_password != confirm_password:
        messages.error(request, 'New passwords do not match.')
    elif len(new_password) < 8:
        messages.error(request, 'Password must be at least 8 characters long.')
    else:
        user.set_password(new_password)
        user.save()
        
        # Re-authenticate to prevent logout
        login(request, user)
        messages.success(request, 'Password changed successfully!')
    
    return redirect('core:profile')
