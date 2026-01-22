"""
Django signals for automatic audit logging.
"""

from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict

from core.models import Income, Expense, Vendor, Category, IncomeSource, AuditLog
from core.middleware.audit import get_current_request


# Fields to exclude from audit logging
EXCLUDED_FIELDS = ['created_at', 'updated_at', 'password']


def get_model_dict(instance, fields=None):
    """Convert model instance to dictionary for audit logging."""
    data = model_to_dict(instance, fields=fields)
    # Convert non-serializable types
    for key, value in data.items():
        if hasattr(value, 'isoformat'):
            data[key] = value.isoformat()
        elif hasattr(value, 'id'):
            data[key] = str(value)
    return data


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
    return '; '.join(changes)


class AuditableMixin:
    """Mixin to track original values for audit."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_data = self._get_audit_data() if self.pk else {}
    
    def _get_audit_data(self):
        return get_model_dict(self)


# Pre-save signal to capture old values
@receiver(pre_save, sender=Income)
@receiver(pre_save, sender=Expense)
@receiver(pre_save, sender=Vendor)
@receiver(pre_save, sender=Category)
@receiver(pre_save, sender=IncomeSource)
def capture_old_values(sender, instance, **kwargs):
    """Capture old values before save for audit trail."""
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
@receiver(post_save, sender=Vendor)
@receiver(post_save, sender=Category)
@receiver(post_save, sender=IncomeSource)
def create_audit_log(sender, instance, created, **kwargs):
    """Create audit log entry after save."""
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    
    if user and not user.is_authenticated:
        user = None
    
    new_data = get_model_dict(instance)
    old_data = getattr(instance, '_old_data', None)
    
    if created:
        action = AuditLog.ActionType.CREATE
        changes_summary = f"Created {sender.__name__}: {str(instance)}"
    else:
        # Check if this is a soft delete
        if hasattr(instance, 'is_soft_deleted') and old_data:
            if not old_data.get('is_soft_deleted') and instance.is_soft_deleted:
                action = AuditLog.ActionType.SOFT_DELETE
                changes_summary = f"Soft deleted {sender.__name__}: {str(instance)}"
            elif old_data.get('is_soft_deleted') and not instance.is_soft_deleted:
                action = AuditLog.ActionType.RESTORE
                changes_summary = f"Restored {sender.__name__}: {str(instance)}"
            else:
                action = AuditLog.ActionType.UPDATE
                changes_summary = get_changes(old_data, new_data) if old_data else ''
        else:
            action = AuditLog.ActionType.UPDATE
            changes_summary = get_changes(old_data, new_data) if old_data else ''
    
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
    except Exception:
        # Don't let audit logging break the main operation
        pass


# Pre-delete signal for logging
@receiver(pre_delete, sender=Income)
@receiver(pre_delete, sender=Expense)
@receiver(pre_delete, sender=Vendor)
@receiver(pre_delete, sender=Category)
@receiver(pre_delete, sender=IncomeSource)
def log_deletion(sender, instance, **kwargs):
    """Log permanent deletion."""
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
    except Exception:
        pass
