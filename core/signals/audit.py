"""
Django signals for automatic audit logging.
Captures all CRUD operations for auditable models.
"""

from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model
from decimal import Decimal

from core.models import Income, Expense, ExpenseBill, Vendor, Category, IncomeSource, AuditLog, RecurringBill, BillPayment
from core.middleware.audit import get_current_request

User = get_user_model()

# Fields to exclude from audit logging
EXCLUDED_FIELDS = ['created_at', 'updated_at', 'password', 'last_login', 'groups', 'user_permissions']

# Global flag to temporarily disable audit logging
SKIP_AUDIT_LOGGING = False


def get_model_dict(instance, fields=None):
    """Convert model instance to dictionary for audit logging."""
    try:
        data = model_to_dict(instance, fields=fields)
        # Convert non-serializable types
        for key, value in list(data.items()):
            if hasattr(value, 'isoformat'):
                data[key] = value.isoformat()
            elif hasattr(value, 'id'):
                data[key] = str(value)
            elif isinstance(value, bytes):
                data[key] = '<binary data>'
            elif isinstance(value, Decimal):
                data[key] = str(value)
        return data
    except Exception:
        return {'id': instance.pk, 'str': str(instance)}


def get_changes(old_data, new_data):
    """Get changes between old and new data."""
    changes = []
    all_keys = set(old_data.keys()) | set(new_data.keys())
    for key in all_keys:
        if key in EXCLUDED_FIELDS:
            continue
        old_val = old_data.get(key)
        new_val = new_data.get(key)
        if old_val != new_val:
            changes.append(f"{key}: '{old_val}' → '{new_val}'")
    return '; '.join(changes) if changes else 'No field changes detected'


# All models to audit
AUDITABLE_MODELS = [Income, Expense, ExpenseBill, Vendor, Category, IncomeSource, RecurringBill, BillPayment, User]


# Pre-save signal to capture old values
@receiver(pre_save, sender=Income)
@receiver(pre_save, sender=Expense)
@receiver(pre_save, sender=ExpenseBill)
@receiver(pre_save, sender=Vendor)
@receiver(pre_save, sender=Category)
@receiver(pre_save, sender=IncomeSource)
@receiver(pre_save, sender=RecurringBill)
@receiver(pre_save, sender=BillPayment)
@receiver(pre_save, sender=User)
def capture_old_values(sender, instance, **kwargs):
    """Capture old values before save for audit trail."""
    import core.signals.audit as audit_module
    if audit_module.SKIP_AUDIT_LOGGING or kwargs.get('raw'):
        return
        
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_data = get_model_dict(old_instance)
        except sender.DoesNotExist:
            instance._old_data = None
    else:
        instance._old_data = None


# Post-save signal to create audit log
@receiver(post_save, sender=Income)
@receiver(post_save, sender=Expense)
@receiver(post_save, sender=ExpenseBill)
@receiver(post_save, sender=Vendor)
@receiver(post_save, sender=Category)
@receiver(post_save, sender=IncomeSource)
@receiver(post_save, sender=RecurringBill)
@receiver(post_save, sender=BillPayment)
@receiver(post_save, sender=User)
def create_audit_log(sender, instance, created, **kwargs):
    """Create audit log entry after save."""
    import core.signals.audit as audit_module
    if audit_module.SKIP_AUDIT_LOGGING or kwargs.get('raw'):
        return
        
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    
    if user and not user.is_authenticated:
        user = None
    
    new_data = get_model_dict(instance)
    old_data = getattr(instance, '_old_data', None)
    
    changes_summary = ''
    action = AuditLog.ActionType.UPDATE
    
    if created:
        action = AuditLog.ActionType.CREATE
        changes_summary = f"Created {sender.__name__}: {str(instance)}"
    else:
        # Check if this is a soft delete
        if hasattr(instance, 'is_soft_deleted') and old_data:
            if not old_data.get('is_soft_deleted') and getattr(instance, 'is_soft_deleted', False):
                action = AuditLog.ActionType.SOFT_DELETE
                changes_summary = f"Soft deleted {sender.__name__}: {str(instance)}"
            elif old_data.get('is_soft_deleted') and not getattr(instance, 'is_soft_deleted', False):
                action = AuditLog.ActionType.RESTORE
                changes_summary = f"Restored {sender.__name__}: {str(instance)}"
            else:
                # Check for approval status changes
                if hasattr(instance, 'status') and 'status' in old_data:
                    old_status = old_data.get('status')
                    new_status = getattr(instance, 'status', None)
                    if old_status != new_status:
                        if new_status == 'approved':
                            action = AuditLog.ActionType.APPROVE
                            changes_summary = f"Approved {sender.__name__}: {str(instance)}"
                        elif new_status == 'rejected':
                            action = AuditLog.ActionType.REJECT
                            changes_summary = f"Rejected {sender.__name__}: {str(instance)}"
                        else:
                            action = AuditLog.ActionType.UPDATE
                            changes_summary = get_changes(old_data, new_data)
                    else:
                        action = AuditLog.ActionType.UPDATE
                        changes_summary = get_changes(old_data, new_data)
                else:
                    action = AuditLog.ActionType.UPDATE
                    changes_summary = get_changes(old_data, new_data)
        else:
            action = AuditLog.ActionType.UPDATE
            changes_summary = get_changes(old_data, new_data) if old_data else f"Updated {sender.__name__}: {str(instance)}"
    
    try:
        AuditLog.log_action(
            user=user,
            action=action,
            model_name=sender.__name__,
            object_id=instance.pk,
            object_repr=str(instance),
            old_values=old_data,
            new_values=new_data,
            changes_summary=changes_summary,
            ip_address=getattr(request, 'client_ip', None) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            request_path=request.path if request else '',
            request_method=request.method if request else '',
        )
        print(f"DEBUG: Audit log created for {sender.__name__} {action}")
    except Exception as e:
        print(f"Audit log error: {e}")
        import traceback
        traceback.print_exc()


# Pre-delete signal for logging
@receiver(pre_delete, sender=Income)
@receiver(pre_delete, sender=Expense)
@receiver(pre_delete, sender=ExpenseBill)
@receiver(pre_delete, sender=Vendor)
@receiver(pre_delete, sender=Category)
@receiver(pre_delete, sender=IncomeSource)
@receiver(pre_delete, sender=RecurringBill)
@receiver(pre_delete, sender=BillPayment)
@receiver(pre_delete, sender=User)
def log_deletion(sender, instance, **kwargs):
    """Log permanent deletion."""
    import core.signals.audit as audit_module
    if audit_module.SKIP_AUDIT_LOGGING or kwargs.get('raw'):
        return
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    
    if user and not user.is_authenticated:
        user = None
    
    try:
        AuditLog.log_action(
            user=user,
            action=AuditLog.ActionType.DELETE,
            model_name=sender.__name__,
            object_id=instance.pk,
            object_repr=str(instance),
            old_values=get_model_dict(instance),
            new_values=None,
            changes_summary=f"Permanently deleted {sender.__name__}: {str(instance)}",
            ip_address=getattr(request, 'client_ip', None) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            request_path=request.path if request else '',
            request_method=request.method if request else '',
        )
    except Exception as e:
        print(f"Audit log error: {e}")


# Login/Logout signals
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login."""
    try:
        AuditLog.log_action(
            user=user,
            action=AuditLog.ActionType.LOGIN,
            model_name='User',
            object_id=user.pk,
            object_repr=user.username,
            old_values=None,
            new_values={'username': user.username, 'role': getattr(user, 'role', '')},
            changes_summary=f"User '{user.username}' logged in",
            ip_address=getattr(request, 'client_ip', None) if hasattr(request, 'client_ip') else request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            request_path=request.path,
            request_method=request.method,
        )
    except Exception as e:
        print(f"Audit log error on login: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout."""
    if user:
        try:
            AuditLog.log_action(
                user=user,
                action=AuditLog.ActionType.LOGOUT,
                model_name='User',
                object_id=user.pk,
                object_repr=user.username,
                old_values=None,
                new_values=None,
                changes_summary=f"User '{user.username}' logged out",
                ip_address=getattr(request, 'client_ip', None) if hasattr(request, 'client_ip') else request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_path=request.path,
                request_method=request.method,
            )
        except Exception as e:
            print(f"Audit log error on logout: {e}")

