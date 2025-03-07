from django.shortcuts import render

# Create your views here.


def home(request):
    return render(request,'inicio.html')

def local(request):
    return render(request,'local.html')
