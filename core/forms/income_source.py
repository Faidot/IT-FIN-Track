"""
Income Source form for IT FIN Track.
"""

from django import forms
from core.models import IncomeSource


class IncomeSourceForm(forms.ModelForm):
    """Form for creating/editing income sources."""
    
    class Meta:
        model = IncomeSource
        fields = [
            'name', 'description', 'icon', 'color',
            'contact_person', 'contact_phone', 'contact_email', 'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Company Accounts'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Description of this source'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-building'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact person name'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
