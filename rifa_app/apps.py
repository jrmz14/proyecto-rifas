from django.apps import AppConfig

class RifaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rifa_app'
    
    def ready(self):
        import rifa_app.signals

