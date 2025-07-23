from django.urls import path
from . import views

app_name = 'noticias'

urlpatterns = [
    path('', views.lista_noticias, name='lista'),
    path('<int:noticia_id>/', views.detalhe_noticia, name='detalhe'),
]