from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from wb.views import *

urlpatterns = [
    path('parser/', GenerateHtmlView.as_view(), name='generated-page'),
    path('search/', TemplateView.as_view(template_name = 'search.html'), name = 'search'),
    path('analitic/', ProductSearchView.as_view(), name='product_search'),
    path('', ProductsView.as_view())
]