from django.urls import path
from . import views

app_name = 'ai_audio'

urlpatterns = [
    path('', views.audio_generator_view, name='audio_generator'),
]
