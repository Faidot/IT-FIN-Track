"""
Income form for IT FIN Track.
"""

from django import forms
from core.models import Income, IncomeSource


class IncomeForm(forms.ModelForm):
    """Form for creating/editing income records."""
    
    source = forms.ModelChoiceField(
        queryset=IncomeSource.objects.filter(is_soft_deleted=False, is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select the income source'
    )
    
    class Meta:
        model = Income
        fields = [
            'source', 'source_detail', 'amount', 'date',
            'payment_mode', 'reference_number', 'project',
            'description', 'is_reimbursable'
        ]
        widgets = {
            'source_detail': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Person name'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction ID, Voucher No.'}),
            'project': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project or purpose'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
            'is_reimbursable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
