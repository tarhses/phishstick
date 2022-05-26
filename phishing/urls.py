from django.urls import path

import phishing.views as views

urlpatterns = [
    path('logo.png', views.opened, name='opened'),
    path('login', views.clicked, name='clicked'),
    path('submit', views.phished, name='phished'),
]
