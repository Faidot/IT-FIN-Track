"""
System management views for backup and restore functionality.
"""

import os
import io
import json
import zipfile
import tempfile
import shutil
from datetime import datetime
from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.utils.text import slugify

def is_system_admin(user):
    """Check if user is a superuser or has admin role."""
    return user.is_active and (user.is_superuser or getattr(user, 'is_admin', False))

@user_passes_test(is_system_admin)
def backup_view(request):
    """
    Generate a full system backup (Database + Media).
    Returns a ZIP file download.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'download_backup':
            # Create a temporary directory for the backup
            with tempfile.TemporaryDirectory() as temp_dir:
                # 1. Dump Database
                db_file_path = os.path.join(temp_dir, 'db.json')
                with open(db_file_path, 'w') as f:
                    call_command('dumpdata', exclude=['auth.permission', 'contenttypes'], stdout=f)
                
                # 2. Create ZIP file
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                zip_filename = f'itfintrack_backup_{timestamp}.zip'
                
                # Create an in-memory zip file
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add database dump
                    zip_file.write(db_file_path, 'db.json')
                    
                    # Add media files
                    media_root = settings.MEDIA_ROOT
                    if os.path.exists(media_root):
                        for root, dirs, files in os.walk(media_root):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Calculate relative path for zip (e.g., media/profile_pics/image.jpg)
                                relative_path = os.path.relpath(file_path, settings.BASE_DIR)
                                zip_file.write(file_path, relative_path)
                
                # Prepare response
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                return response
                
    return render(request, 'core/system/backup_restore.html')

@user_passes_test(is_system_admin)
def restore_view(request):
    """
    Restore system from a backup ZIP file.
    Warning: This overwrites existing data!
    """
    if request.method == 'POST':
        backup_file = request.FILES.get('backup_file')
        
        if not backup_file:
            messages.error(request, 'Please select a backup file to upload.')
            return HttpResponseRedirect(reverse('core:system_backup'))
            
        if not backup_file.name.endswith('.zip'):
            messages.error(request, 'Invalid file format. Please upload a ZIP file.')
            return HttpResponseRedirect(reverse('core:system_backup'))
            
        try:
            # Create a temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save uploaded file
                temp_zip_path = os.path.join(temp_dir, 'upload.zip')
                with open(temp_zip_path, 'wb+') as destination:
                    for chunk in backup_file.chunks():
                        destination.write(chunk)
                
                # Extract ZIP
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # 1. Restore Database
                db_file_path = os.path.join(temp_dir, 'db.json')
                if os.path.exists(db_file_path):
                    import core.signals.audit as audit_signals
                    try:
                        # Disable audit logging during restore to prevent transaction errors
                        audit_signals.SKIP_AUDIT_LOGGING = True
                        
                        # Manually delete all data to ensure clean state
                        # flush command can be problematic in some environments/configurations
                        from django.apps import apps
                        
                        # Get all models from our apps
                        # We focus on 'core' app to avoid deleting auth/contenttypes if not needed
                        # But for full restore, we might want to be thorough.
                        # However, deleting auth.Permission contenttypes.ContentType can break things.
                        # Let's target the core app models specifically + auth.User
                        
                        target_apps = ['core']
                        for app_config in apps.get_app_configs():
                            if app_config.label in target_apps:
                                for model in app_config.get_models():
                                    try:
                                        model.objects.all().delete()
                                    except Exception:
                                        pass
                        
                        # Also clear users if they are not in core (they are custom user in core, so covered above)
                        # But if we used default auth.User, we'd need to clear that too.
                        # Our custom user is core.User, so it's covered.
                        
                        # Load data
                        call_command('loaddata', db_file_path)
                        # messages.success(request, 'Database restored successfully.')
                    except Exception as e:
                        messages.error(request, f'Database restore failed: {str(e)}')
                        return HttpResponseRedirect(reverse('core:system_backup'))
                    finally:
                        # Re-enable audit logging
                        audit_signals.SKIP_AUDIT_LOGGING = False
                else:
                    messages.warning(request, 'No db.json found in backup. Database not restored.')
                
                # 2. Restore Media
                # The zip structure for media should be checked.
                # In backup, we stored as 'media/...' relative to BASE_DIR.
                # So if we extract, we might get a 'media' folder in temp_dir.
                
                extracted_media_dir = os.path.join(temp_dir, 'media')
                if os.path.exists(extracted_media_dir):
                    target_media_root = settings.MEDIA_ROOT
                    
                    # Ensure target exists
                    os.makedirs(target_media_root, exist_ok=True)
                    
                    # Copy files using shutil
                    # This merges/overwrites files in MEDIA_ROOT
                    # Iterate to handle potential subdirectories clearly
                    for root, dirs, files in os.walk(extracted_media_dir):
                        for file in files:
                            src_file = os.path.join(root, file)
                            
                            # Determine relative path from extracted 'media' root
                            rel_path = os.path.relpath(src_file, extracted_media_dir)
                            
                            # Target path
                            dst_file = os.path.join(target_media_root, rel_path)
                            
                            # Build directories if needed
                            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                            
                            # Copy
                            shutil.copy2(src_file, dst_file)
                            
                    # messages.success(request, 'Media files restored successfully.')
                else:
                    # Logic to handle if media was zipped without 'media' prefix or empty
                    # For now, we assume the format from backup_view
                    pass

            messages.success(request, 'System restore completed successfully!')
            
        except Exception as e:
            messages.error(request, f'Critical error during restore: {str(e)}')
            
        return HttpResponseRedirect(reverse('core:system_backup'))
        
    # If GET, redirect to main backup page (or show a separate restore page)
    return HttpResponseRedirect(reverse('core:system_backup'))
