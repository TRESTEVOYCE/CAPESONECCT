from django.apps import AppConfig

class AdminsideConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'AdminSide'

    def ready(self):
        import AdminSide.signals 