from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path("projects/<int:project_id>/", views.project_detail),
    path("projects/new/", views.project_new),
    path("projects/join/", views.project_join),
    path("runs/<int:run_id>/", views.run_detail),
]
