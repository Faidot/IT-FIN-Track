"""
Management command to create initial data for IT FIN Track.
"""

from django.core.management.base import BaseCommand
from core.models import User, Category


class Command(BaseCommand):
    help = 'Creates initial data for IT FIN Track'
    
    def handle(self, *args, **options):
        # Create admin user if not exists
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@itfintrack.local',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role='admin',
                department='IT'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: admin / admin123'))
        
        # Create sample users
        if not User.objects.filter(username='executive').exists():
            User.objects.create_user(
                username='executive',
                email='executive@itfintrack.local',
                password='exec123',
                first_name='IT',
                last_name='Executive',
                role='executive',
                department='IT'
            )
            self.stdout.write(self.style.SUCCESS(f'Created executive user: executive / exec123'))
        
        if not User.objects.filter(username='manager').exists():
            User.objects.create_user(
                username='manager',
                email='manager@itfintrack.local',
                password='mgr123',
                first_name='Finance',
                last_name='Manager',
                role='manager',
                department='Finance'
            )
            self.stdout.write(self.style.SUCCESS(f'Created manager user: manager / mgr123'))
        
        # Create default categories
        default_categories = Category.get_default_categories()
        created_count = 0
        for cat_data in default_categories:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data.get('icon', 'fa-folder'),
                    'description': cat_data.get('description', ''),
                    'color': '#FF6B01'
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} categories'))
        self.stdout.write(self.style.SUCCESS('Initial data setup complete!'))
