from django.shortcuts import render
from django.db.models import Count
from grupos.models import Grupo
from noticias.models import Noticia
from votacao.models import Voto, ResultadoVotacao


def home(request):
    """Home page with dashboard overview"""
    
    # Get statistics
    total_grupos = Grupo.objects.filter(ativo=True).count()
    grupos_escola_samba = Grupo.objects.filter(ativo=True, categoria='escola_samba').count()
    grupos_bloco_rua = Grupo.objects.filter(ativo=True, categoria='bloco_rua').count()
    
    # Get recent news
    noticias_destaque = Noticia.objects.filter(
        publicada=True, 
        destaque=True
    ).order_by('-data_publicacao')[:3]
    
    noticias_recentes = Noticia.objects.filter(
        publicada=True
    ).exclude(
        id__in=noticias_destaque.values_list('id', flat=True)
    ).order_by('-data_publicacao')[:5]
    
    # Get voting stats
    total_votos = Voto.objects.count()
    
    # Get top voted groups
    top_grupos = Grupo.objects.filter(ativo=True).annotate(
        total_votos=Count('votos')
    ).order_by('-total_votos')[:5]
    
    # Get featured groups (random selection)
    grupos_destaque = Grupo.objects.filter(ativo=True).order_by('?')[:6]
    
    context = {
        'total_grupos': total_grupos,
        'grupos_escola_samba': grupos_escola_samba,
        'grupos_bloco_rua': grupos_bloco_rua,
        'total_votos': total_votos,
        'noticias_destaque': noticias_destaque,
        'noticias_recentes': noticias_recentes,
        'top_grupos': top_grupos,
        'grupos_destaque': grupos_destaque,
    }
    
    return render(request, 'core/home.html', context)
