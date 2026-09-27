from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("verify/", views.verify, name="verify"),
    path("trace/<str:code>/", views.trace, name="trace"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("batch/<str:code>/", views.batch_detail, name="batch_detail"),
    path("hives/new/", views.new_hive, name="new_hive"),
    path("batches/new/", views.new_batch, name="new_batch"),
    path("batch/<str:code>/add-event/", views.add_event, name="add_event"),
    path("api/batch/<str:code>/", views.api_batch, name="api_batch"),
]
