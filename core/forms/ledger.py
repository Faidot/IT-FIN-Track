"""
Forms for Ledger management.
"""

from django import forms
from core.models import Ledger, LedgerEntry


class LedgerForm(forms.ModelForm):
    """Form for creating and editing ledgers."""
    
    class Meta:
        model = Ledger
        fields = ['name', 'ledger_type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ledger name'}),
            'ledger_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Description'}),
        }


class LedgerEntryForm(forms.ModelForm):
    """Form for creating ledger entries."""
    
    class Meta:
        model = LedgerEntry
        fields = ['ledger', 'entry_type', 'amount', 'date', 'description', 'reference']
        widgets = {
            'ledger': forms.Select(attrs={'class': 'form-select'}),
            'entry_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Entry description'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reference number'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
