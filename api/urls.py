from django.urls import path
from . import views

urlpatterns = [
    path('find_company_news/', views.find_company_news, name='find_company_news'), # finds new company news in the internet
    path('get_company_news/', views.get_company_news, name='get_company_news') # fetches company news from the database
]
