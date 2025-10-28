from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from wb.views import *

urlpatterns = [
    path('parser/', GenerateHtmlView.as_view(), name='generated-page'),
    path('analitic/', ProductSearchView.as_view(), name='product_search'),
    path('', ProductsView.as_view())
]