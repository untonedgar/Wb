from django.shortcuts import render
from django.views import View
from django.views.generic import ListView
from wb.utils.parser import WildberriesParser
from wb.utils.handler_link import handler
from wb.models import Product
from django_elasticsearch_dsl.search import Search
from elasticsearch_dsl import Q
from django.db import models
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Match, Fuzzy
from elasticsearch_dsl.connections import connections
from elasticsearch import ApiError, ConnectionError as ESConnectionError


class GenerateHtmlView(View):
    """Генерирует HTML-страницу с динамическим контентом"""

    def get_initial_data(self, request):
        user_text = request.GET.get('user_text', '')
        if not user_text:
            return {}
        else:
            user_text = handler(user_text)
            self.parser = WildberriesParser()
            self.parser.parse(f'{user_text}')

    def get(self, request):
        context = self.get_initial_data(request)
        return render(request, 'main.html', context)


class ProductsView(ListView):
    model = Product
    template_name = 'products.html'
    context_object_name = 'products'


class ProductSearchView(ListView):
    template_name = 'statistic.html'
    context_object_name = 'products'
    paginate_by = 50

    def get_queryset(self):

        try:
            # Проверяем подключение
            from elasticsearch_dsl.connections import connections
            es = connections.get_connection('default')

            if not es.ping():
                raise ConnectionError("Elasticsearch не доступен")

            query = self.request.GET.get('q', '').strip()

            if not query:
                return Product.objects.none()

            # 1. Поиск в Elasticsearch
            search = Search(index='products').extra(size=1000)

            # Основной запрос с исправлением ошибок
            search_query = Q(
                'bool',
                should=[
                    # Точное совпадение (максимальный вес)
                    Q('match_phrase', name={'query': query, 'boost': 3}),

                    # Нечеткий поиск с авто-исправлением
                    Q('match', name={
                        'query': query,
                        'fuzziness': 'AUTO',
                        'operator': 'or',
                        'analyzer': 'russian'
                    }),

                    # Поиск по N-граммам для частичных совпадений
                    Q('match', name__ngram={
                        'query': query,
                        'boost': 0.5
                    })
                ],
                minimum_should_match=1
            )

            search = search.query(search_query)

            try:
                results = search.execute()
            except Exception as e:
                print(f"Elasticsearch error: {e}")
                return Product.objects.none()

            # 2. Получаем article найденных товаров
            product_articles = [hit.article for hit in results]

            if not product_articles:
                return Product.objects.none()

            # 3. Сохраняем порядок из Elasticsearch
            order = {article: idx for idx, article in enumerate(product_articles)}

            return Product.objects.filter(article__in=product_articles).annotate(
                search_order=models.Case(
                    *[models.When(article=art, then=pos) for art, pos in order.items()],
                    default=len(order),
                    output_field=models.IntegerField()
                )
            ).order_by('search_order')
        except (ApiError, ESConnectionError) as e:
            import logging
            logging.error(f"Elasticsearch error: {str(e)}")
            return self.model.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

