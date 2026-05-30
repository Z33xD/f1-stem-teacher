from django.urls import path
from . import views

urlpatterns = [
    path('chatbot/', views.chat),
    path('chatbot/chat/', views.chat_endpoint, name='chat_endpoint') #,
    # path('chatbot/general/', views.general_chat, name='general_chat'),
    # path('chatbot/general/chat/', views.general_chat_endpoint, name='general_chat_endpoint'),
]
