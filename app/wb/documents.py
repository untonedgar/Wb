from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from wb.models import Product


@registry.register_document
class ProductDocument(Document):
    article = fields.LongField()
    name = fields.TextField(
        analyzer='russian',
        fields={
            'raw': fields.KeywordField(),
            'suggest': fields.CompletionField(),
            'ngram': fields.TextField(
                analyzer='edge_ngram_analyzer'
            )
        }
    )

    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 2,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'russian': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'russian_stemmer']
                    },
                    'edge_ngram_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'edge_ngram_filter']
                    }
                },
                'filter': {
                    'russian_stemmer': {
                        'type': 'stemmer',
                        'language': 'russian'
                    },

                    'edge_ngram_filter': {
                        'type': 'edge_ngram',
                        'min_gram': 2,
                        'max_gram': 15
                    },

                }
            }
        }

    class Django:
        model = Product
        fields = [
            'price',
            'old_price',
            'rating',
            'reviews'
        ]

    def prepare_price(self, instance):
        """Преобразование цены для индексации"""
        return float(instance.price) if instance.price else 0.0

    def prepare_old_price(self, instance):
        """Обработка случая, когда old_price может быть None"""
        return float(instance.old_price) if instance.old_price else None