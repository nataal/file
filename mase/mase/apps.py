from django.apps import AppConfig

class MaseConfig(AppConfig):
    name = 'mase.mase'

    def ready(self):
        import mase.mase.signals