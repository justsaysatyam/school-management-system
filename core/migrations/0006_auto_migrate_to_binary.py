from django.db import migrations, models
import os
from django.conf import settings
import mimetypes

def migrate_files_to_binary(apps, schema_editor):
    # Get models from the current app state
    Admin = apps.get_model('core', 'Admin')
    Teacher = apps.get_model('core', 'Teacher')
    Student = apps.get_model('core', 'Student')
    Notice = apps.get_model('core', 'Notice')
    Event = apps.get_model('core', 'Event')
    SchoolInfo = apps.get_model('core', 'SchoolInfo')
    GalleryImage = apps.get_model('core', 'GalleryImage')

    # Mapping of (Model, old_path_field, new_binary_field)
    # Note: In the data migration, we use the temporary field names we created in RenameField
    models_to_migrate = [
        (Admin, 'photo_old', 'photo'),
        (Teacher, 'photo_old', 'photo'),
        (Student, 'photo_old', 'photo'),
        (Notice, 'file_old', 'file'),
        (Event, 'image_old', 'image'),
        (SchoolInfo, 'logo_old', 'logo'),
        (GalleryImage, 'image_old', 'image'),
    ]

    for model, old_field_name, new_field_name in models_to_migrate:
        for obj in model.objects.all():
            path_value = getattr(obj, old_field_name)
            if path_value:
                # Convert FieldFile or string to string path
                rel_path = str(path_value)
                if not rel_path:
                    continue
                
                # Try to find the file
                file_path = os.path.join(settings.MEDIA_ROOT, rel_path)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as f:
                            data = f.read()
                            setattr(obj, new_field_name, data)
                            # Set metadata
                            mime = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                            setattr(obj, f"{new_field_name}_mimetype", mime)
                            setattr(obj, f"{new_field_name}_filename", os.path.basename(file_path))
                            obj.save()
                    except Exception as e:
                        # Log error but continue
                        print(f"Error migrating {model.__name__} {obj.pk}: {e}")

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_inquiry'),
    ]

    operations = [
        # 1. Add metadata fields
        migrations.AddField(model_name='admin', name='photo_mimetype', field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddField(model_name='admin', name='photo_filename', field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name='teacher', name='photo_mimetype', field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddField(model_name='teacher', name='photo_filename', field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name='student', name='photo_mimetype', field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddField(model_name='student', name='photo_filename', field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name='notice', name='file_mimetype', field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddField(model_name='notice', name='file_filename', field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name='event', name='image_mimetype', field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddField(model_name='event', name='image_filename', field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name='schoolinfo', name='logo_mimetype', field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddField(model_name='schoolinfo', name='logo_filename', field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name='galleryimage', name='image_mimetype', field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddField(model_name='galleryimage', name='image_filename', field=models.CharField(blank=True, max_length=255, null=True)),

        # 2. Rename old fields from ImageField/FileField to temp names
        migrations.RenameField(model_name='admin', old_name='photo', new_name='photo_old'),
        migrations.RenameField(model_name='teacher', old_name='photo', new_name='photo_old'),
        migrations.RenameField(model_name='student', old_name='photo', new_name='photo_old'),
        migrations.RenameField(model_name='notice', old_name='file', new_name='file_old'),
        migrations.RenameField(model_name='event', old_name='image', new_name='image_old'),
        migrations.RenameField(model_name='schoolinfo', old_name='logo', new_name='logo_old'),
        migrations.RenameField(model_name='galleryimage', old_name='image', new_name='image_old'),
        
        # 3. Add new BinaryFields with the original names
        migrations.AddField(model_name='admin', name='photo', field=models.BinaryField(blank=True, null=True)),
        migrations.AddField(model_name='teacher', name='photo', field=models.BinaryField(blank=True, null=True)),
        migrations.AddField(model_name='student', name='photo', field=models.BinaryField(blank=True, null=True)),
        migrations.AddField(model_name='notice', name='file', field=models.BinaryField(blank=True, null=True)),
        migrations.AddField(model_name='event', name='image', field=models.BinaryField(blank=True, null=True)),
        migrations.AddField(model_name='schoolinfo', name='logo', field=models.BinaryField(blank=True, null=True)),
        migrations.AddField(model_name='galleryimage', name='image', field=models.BinaryField(blank=True, null=True)),
        
        # 4. Run the data migration to copy file content to binary fields
        migrations.RunPython(migrate_files_to_binary),

        # 5. Remove the old fields
        migrations.RemoveField(model_name='admin', name='photo_old'),
        migrations.RemoveField(model_name='teacher', name='photo_old'),
        migrations.RemoveField(model_name='student', name='photo_old'),
        migrations.RemoveField(model_name='notice', name='file_old'),
        migrations.RemoveField(model_name='event', name='image_old'),
        migrations.RemoveField(model_name='schoolinfo', name='logo_old'),
        migrations.RemoveField(model_name='galleryimage', name='image_old'),
    ]
