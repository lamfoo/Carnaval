from django.urls import path
from . import views

app_name = 'votacao'

urlpatterns = [
    path('', views.votar, name='votar'),
    path('processar/', views.processar_voto, name='processar_voto'),
    path('resultados/', views.resultados, name='resultados'),
    path('resultados/json/', views.resultados_json, name='resultados_json'),
    path('verificar/', views.verificar_voto, name='verificar_voto'),
]