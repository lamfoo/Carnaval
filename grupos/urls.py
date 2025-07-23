from django.urls import path
from . import views

app_name = 'grupos'

urlpatterns = [
    path('', views.lista_grupos, name='lista'),
    path('<int:grupo_id>/', views.detalhe_grupo, name='detalhe'),
]