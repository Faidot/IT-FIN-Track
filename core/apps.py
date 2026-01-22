"""
Core app configuration.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'IT FIN Track Core'
    
    def ready(self):
        # Import signals to register them
        from core.signals import audit  # noqa
