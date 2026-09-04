from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'Payment Management'
    
    def ready(self):
        """Called when the app is ready"""
        # Import signals here if you have any
        pass