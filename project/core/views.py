from django.shortcuts import render

# Create your views here.


def home(request):
    return render(request,'core/inicio.html')

def local(request):
    return render(request,'core/local.html')
