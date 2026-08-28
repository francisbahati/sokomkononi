from django.apps import AppConfig

class AdminPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_panel'
    verbose_name = 'Platform Administration'
    
    def ready(self):
        """Called when the app is ready"""
        # Import signals here if needed
        pass