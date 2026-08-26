from django.db import migrations


def mark_existing_profiles_verified(apps, schema_editor):
    # Los usuarios que ya existían antes de esta funcionalidad nunca pasaron
    # por el flujo de verificación, así que no tiene sentido pedirles que lo hagan.
    Profile = apps.get_model('store', 'Profile')
    Profile.objects.update(email_verified=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0021_profile_email_verified'),
    ]

    operations = [
        migrations.RunPython(mark_existing_profiles_verified, noop),
    ]
