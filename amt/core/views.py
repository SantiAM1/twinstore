from os import name
from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.


def home(request):
    return render(request,'inicio.html')

def local(request):
    return render(request,'local.html')
