from django.apps import AppConfig

class DealsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'deals'
    verbose_name = 'Deal Management'
    
    def ready(self):
        """Called when the app is ready"""
        # Import signals here if you have any
        pass