"""
Context processors for IT FIN Track.
"""

from django.conf import settings


def theme_colors(request):
    """Make theme colors available in all templates."""
    return {
        'THEME_COLORS': getattr(settings, 'THEME_COLORS', {}),
    }
