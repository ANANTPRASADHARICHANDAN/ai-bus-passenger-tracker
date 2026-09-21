from django.urls import path
from . import views

urlpatterns = [
    path('update-telemetry/', views.update_telemetry, name='update_telemetry'),
    path('get-telemetry/', views.get_latest_telemetry, name='get_telemetry'),
]