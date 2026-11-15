from django.urls import path

from . import views

app_name = 'stocks'

urlpatterns = [
    path('', views.index, name='index'),
    path('analysis/<int:pk>/', views.analysis_detail, name='analysis-detail'),
    path('analysis/<int:pk>/summary/', views.summarize_analysis, name='summary'),
]
