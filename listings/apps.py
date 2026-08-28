from django.apps import AppConfig

class ListingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listings'
    verbose_name = 'Property Listings'
    
    def ready(self):
        """Called when the app is ready"""
        # Import signals here if you have any
        pass