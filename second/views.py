from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render , redirect
from django.views.decorators.cache import never_cache


@never_cache
def dashboard(request):
    return render(request, 'dashboard.html')


