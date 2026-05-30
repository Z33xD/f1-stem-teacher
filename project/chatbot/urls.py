from django.urls import path
from . import views

urlpatterns = [
    path('chatbot/', views.chat),
    path('chatbot/chat/', views.chat_endpoint, name='chat_endpoint')
]
