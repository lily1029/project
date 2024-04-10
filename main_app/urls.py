from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('furniture/', views.furniture_index, name="index"),
    
    path('accounts/signup/', views.signup, name='signup'),

    path('furniture/<int:furniture_item_id>/',views.furniture_detail, name='detail'),
    
]