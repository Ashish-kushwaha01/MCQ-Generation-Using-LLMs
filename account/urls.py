from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('signup/', views.signup, name='signup'), 
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('verify_otp/',views.verify_otp,name='verify_otp'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
]