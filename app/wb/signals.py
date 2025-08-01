from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from wb.documents import ProductDocument
from wb.models import Product
from django.apps import AppConfig
from django_elasticsearch_dsl.registries import registry

@receiver(post_save, sender=Product)
def update_document(sender, instance, **kwargs):
    ProductDocument().update(instance)

@receiver(post_delete, sender=Product)
def delete_document(sender, instance, **kwargs):
    ProductDocument().update(instance, action='delete')


