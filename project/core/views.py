from django.shortcuts import render

def home(request):
    return render(request,'core/home.html',{"name":'home'})

def aboutus(request):
    return render(request,'core/aboutus.html',{"name":'about us'})



