"""
Forms for Vendor management.
"""

from django import forms
from core.models import Vendor


class VendorForm(forms.ModelForm):
    """Form for creating and editing vendors."""
    
    class Meta:
        model = Vendor
        fields = [
            'name', 'contact_person', 'email', 'phone',
            'address', 'gst_number', 'bank_details', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor/Company name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary contact person'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'GST/Tax registration number'}),
            'bank_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Bank account details'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes'}),
        }
