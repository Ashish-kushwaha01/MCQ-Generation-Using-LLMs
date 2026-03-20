from django.urls import path
from . import views

app_name = 'pdf_mcq'

urlpatterns = [
    path('pdf-mcq/', views.pdf_mcq_view, name='pdf_mcq'),
    path('clear-history/', views.clear_history, name='clear_history'),
]