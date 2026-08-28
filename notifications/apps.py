from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Notification Management'
    
    def ready(self):
        """Called when the app is ready"""
        # Import signals here
        import notifications.signals