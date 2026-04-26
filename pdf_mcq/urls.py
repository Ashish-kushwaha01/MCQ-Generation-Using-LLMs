# from django.urls import path
# from . import views

# app_name = 'pdf_mcq'

# urlpatterns = [
#     path('pdf-mcq/', views.pdf_mcq_view, name='pdf_mcq'),
#     path('clear-history/', views.clear_history, name='clear_history'),
# ]




from django.urls import path
from . import views

app_name = 'pdf_mcq'

urlpatterns = [
    path('', views.pdf_mcq_view, name='pdf_mcq'),
    path('clear-history/', views.clear_history, name='clear_history'),
    path('submit-answers/', views.submit_answers, name='submit_answers'),
    path('get-results/<str:session_id>/', views.get_session_results, name='get_results'),
    path('generate-by-topic/', views.generate_by_topic, name='generate_by_topic'),
    path('summarize-topic/', views.summarize_topic_view, name='summarize_topic'),
    path('download-mcqs-pdf/', views.download_mcqs_pdf, name='download_mcqs_pdf'),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
]