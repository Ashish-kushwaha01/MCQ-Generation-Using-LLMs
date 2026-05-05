from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render , redirect
from django.views.decorators.cache import never_cache


@never_cache
def dashboard(request):
    return render(request, 'dashboard.html')

def about(request):
    return render(request, 'static_pages/about.html')

def faq(request):
    return render(request, 'static_pages/faq.html')

def contact(request):
    return render(request, 'static_pages/contact.html')

def terms(request):
    return render(request, 'static_pages/terms.html')

def privacy(request):
    return render(request, 'static_pages/privacy.html')



