from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "homepage"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/papers/", views.papers_api, name="papers_api"),
]
