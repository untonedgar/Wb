from django.apps import AppConfig
from django_elasticsearch_dsl.registries import registry


class WbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wb'

    def ready(self):
        # Инициализация подключения при запуске приложения
        from elasticsearch_dsl import connections
        from django.conf import settings

        connections.create_connection(
            alias='default',
            hosts=settings.ELASTICSEARCH_DSL['default']['hosts'],
            timeout=settings.ELASTICSEARCH_DSL['default']['timeout']
        )

