from django.urls import path, include
from . import views

app_name = 'test_all'

urlpatterns =[
    path('test_page/', views.test_page, name='test_page'),
    path('general_info/<slug:slug>/', views.general_info, name='general_info'),
    # path('load_questions/<slug:slug>/<int:q_no>/', views.load_questions, name='load_questions'),
    # path('restart/<slug:slug>/', views.restart_test, name='restart'),        
    path('result/<slug:slug>/<int:attempt_id>', views.test_result, name='result'),
    path('test/<slug:slug>/start/', views.start_test, name='start_test'),
    path('test/<slug:slug>/attempt/<int:attempt_id>', views.question_page, name='question_page'),
    path('test/<slug:slug>/ajax/question/<int:attempt_id>', views.ajax_question, name='ajax_question'),
    path('test/<slug:slug>/ajax/save/<int:attempt_id>', views.ajax_save_answer, name='ajax_save'),
    # path('test/<slug:slug>/ajax/result/', views.ajax_result, name='ajax_result'),

]