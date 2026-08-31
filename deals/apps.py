from django.apps import AppConfig


class DealsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'deals'
    verbose_name = 'Deal Management'

    def ready(self):
        # Import signals to register them – this no longer causes an ImportError
        import deals.signals