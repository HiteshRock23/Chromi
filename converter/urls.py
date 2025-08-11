from django.urls import path
from . import views

app_name = 'converter'

urlpatterns = [
    path('', views.home, name='home'),
    path('convert/', views.convert_video, name='convert_video'),
    path('health/', views.health_check, name='health_check'),
    path('jobs/<str:job_id>/', views.job_status, name='job_status'),
]