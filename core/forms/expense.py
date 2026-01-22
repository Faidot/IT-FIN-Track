"""
Forms for Expense management.
"""

from django import forms
from core.models import Expense, ExpenseBill


class ExpenseForm(forms.ModelForm):
    """Form for creating and editing expense records."""
    
    class Meta:
        model = Expense
        fields = [
            'category', 'vendor', 'linked_income', 'amount', 'date',
            'description', 'purpose', 'invoice_number'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'linked_income': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the expense...'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project or purpose'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Invoice/Bill number'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make vendor and linked_income optional in the form
        self.fields['vendor'].required = False
        self.fields['linked_income'].required = False
        self.fields['vendor'].empty_label = "-- Select Vendor (Optional) --"
        self.fields['linked_income'].empty_label = "-- Select Income Source (Optional) --"
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount


class ExpenseBillForm(forms.ModelForm):
    """Form for uploading expense bills."""
    
    class Meta:
        model = ExpenseBill
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bill description (optional)'}),
        }


class MultipleFileInput(forms.ClearableFileInput):
    """Widget for multiple file uploads."""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Field for handling multiple file uploads."""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}))
        super().__init__(*args, **kwargs)
    
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class ExpenseWithBillsForm(ExpenseForm):
    """Extended expense form with multiple bill uploads."""
    
    bills = MultipleFileField(required=False, label='Bills/Invoices')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bills'].widget.attrs.update({
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'multiple': True,
        })
