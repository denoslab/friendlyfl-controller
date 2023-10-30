from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path("projects/<int:project_id>/<int:site_id>/", views.project_detail),
    path("projects/new/", views.project_new),
    path("projects/join/", views.project_join),
    path("projects/leave/", views.project_leave),
    path("runs/<int:run_id>/", views.run_detail),
    path("runs/detail/<int:batch>/<int:project_id>/<int:site_id>/", views.run_detail),
    path("runs/start/<int:project_id>/<int:site_id>/", views.start_runs),
    path("runs/dataset/", views.upload_dataset),
    path("runs/action/<int:run_id>/<int:project_id>/<int:batch>/<str:role>/<str:action>/",
         views.perform_run_action),
    path("runs/fetch_logs/",
         views.fetch_logs),
]
