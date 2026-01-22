"""
Add IncomeSource model and migrate existing Income data.
"""

from django.db import migrations, models
import django.db.models.deletion


def create_default_sources(apps, schema_editor):
    """Create default income sources."""
    IncomeSource = apps.get_model('core', 'IncomeSource')
    
    defaults = [
        {'name': 'Company Accounts', 'icon': 'fa-building', 'color': '#4E4E4E', 'description': 'Funds from company accounts department'},
        {'name': 'Manager Advance', 'icon': 'fa-user-tie', 'color': '#17A2B8', 'description': 'Advance cash from manager for purchases'},
        {'name': 'Personal Money', 'icon': 'fa-wallet', 'color': '#FFC107', 'description': 'Employee personal money used for work'},
        {'name': 'Vendor Refund', 'icon': 'fa-undo', 'color': '#28A745', 'description': 'Refunds received from vendors'},
        {'name': 'Project Fund', 'icon': 'fa-project-diagram', 'color': '#6F42C1', 'description': 'Specific project or client funded amount'},
        {'name': 'Other', 'icon': 'fa-plus-circle', 'color': '#FF6B01', 'description': 'Miscellaneous income sources'},
    ]
    
    for source_data in defaults:
        IncomeSource.objects.get_or_create(
            name=source_data['name'],
            defaults=source_data
        )


def migrate_income_sources(apps, schema_editor):
    """Migrate existing Income records to use new IncomeSource FK."""
    Income = apps.get_model('core', 'Income')
    IncomeSource = apps.get_model('core', 'IncomeSource')
    
    # Map old source choices to new IncomeSource names
    source_mapping = {
        'company': 'Company Accounts',
        'manager': 'Manager Advance',
        'personal': 'Personal Money',
        'refund': 'Vendor Refund',
        'other': 'Other',
    }
    
    # Get or create default source for fallback
    other_source, _ = IncomeSource.objects.get_or_create(
        name='Other',
        defaults={'icon': 'fa-plus-circle', 'color': '#FF6B01'}
    )
    
    # Update all existing Income records
    for income in Income.objects.all():
        if hasattr(income, 'source_old') and income.source_old:
            source_name = source_mapping.get(income.source_old, 'Other')
            try:
                income_source = IncomeSource.objects.get(name=source_name)
            except IncomeSource.DoesNotExist:
                income_source = other_source
            income.source_new = income_source
            income.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Step 1: Create IncomeSource model
        migrations.CreateModel(
            name='IncomeSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the income source', max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text='Description of this income source')),
                ('icon', models.CharField(default='fa-money-bill', help_text='Font Awesome icon class (e.g., fa-building)', max_length=50)),
                ('color', models.CharField(default='#FF6B01', help_text='Color for this source (hex code)', max_length=7)),
                ('contact_person', models.CharField(blank=True, help_text='Contact person for this source', max_length=100)),
                ('contact_phone', models.CharField(blank=True, help_text='Contact phone number', max_length=20)),
                ('contact_email', models.EmailField(blank=True, help_text='Contact email', max_length=254)),
                ('notes', models.TextField(blank=True, help_text='Additional notes')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this source is active')),
                ('is_soft_deleted', models.BooleanField(default=False, help_text='Soft delete flag')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Income Source',
                'verbose_name_plural': 'Income Sources',
                'ordering': ['name'],
            },
        ),
        
        # Step 2: Create default income sources
        migrations.RunPython(create_default_sources),
        
        # Step 3: Rename old source field
        migrations.RenameField(
            model_name='income',
            old_name='source',
            new_name='source_old',
        ),
        
        # Step 4: Add new source FK as nullable
        migrations.AddField(
            model_name='income',
            name='source_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='incomes_temp',
                to='core.incomesource',
            ),
        ),
        
        # Step 5: Migrate data
        migrations.RunPython(migrate_income_sources),
        
        # Step 6: Remove old source field
        migrations.RemoveField(
            model_name='income',
            name='source_old',
        ),
        
        # Step 7: Rename new source field and make required
        migrations.RenameField(
            model_name='income',
            old_name='source_new',
            new_name='source',
        ),
        
        # Step 8: Update field constraints
        migrations.AlterField(
            model_name='income',
            name='source',
            field=models.ForeignKey(
                help_text='Source of the income',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='incomes',
                to='core.incomesource',
            ),
        ),
    ]
