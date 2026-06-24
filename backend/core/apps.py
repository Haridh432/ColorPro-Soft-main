from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_superuser(sender, **kwargs):
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Auto-created admin user.")
    if not User.objects.filter(username='testuser').exists():
        User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        print("Auto-created testuser.")

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        post_migrate.connect(create_default_superuser, sender=self)
