from django.urls import path
from . import views

app_name = 'summarize'
urlpatterns = [

    path(
        "summarize/",views.summarize_video,name="summarize"
    ),

]