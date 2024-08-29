from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,JsonResponse
from .models import Producto, SubCategoria,Categoria,Marca
from django.urls import reverse

# Create your views here.

def home(request):
    return HttpResponse("home")