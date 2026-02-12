# Create initial admin user for the school management system
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

from core.models import Admin, SchoolClass, Subject

# Create admin user
admin_email = 'admin@midpoint.com'
if not Admin.objects.filter(email=admin_email).exists():
    admin = Admin(
        name='Admin User',
        email=admin_email,
        phone='7762044304',
        address='Barahiya, Near Hanuman Temple',
        role='Administrator'
    )
    admin.set_password('admin123')
    admin.save()
    print(f'Admin user created: {admin_email} / admin123')
else:
    print(f'Admin user already exists: {admin_email}')

# Create some default classes
classes_data = [
    ('Class 1', 'A', 30),
    ('Class 2', 'A', 30),
    ('Class 3', 'A', 25),
    ('Class 4', 'A', 25),
    ('Class 5', 'A', 20),
]

for class_name, section, strength in classes_data:
    obj, created = SchoolClass.objects.get_or_create(
        class_name=class_name,
        section=section,
        defaults={'strength': strength}
    )
    if created:
        print(f'Created class: {class_name} - {section}')

# Create some subjects
subjects_data = [
    ('Hindi', 'HIN'),
    ('English', 'ENG'),
    ('Mathematics', 'MATH'),
    ('Science', 'SCI'),
    ('Social Studies', 'SST'),
]

for subject_name, code in subjects_data:
    obj, created = Subject.objects.get_or_create(
        subject_code=code,
        defaults={'subject_name': subject_name}
    )
    if created:
        print(f'Created subject: {subject_name}')

print('\nSetup complete! You can now login with:')
print('Admin: admin@midpoint.com / admin123')
