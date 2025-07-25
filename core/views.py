from django.shortcuts import render
from django.db.models import Count
from grupos.models import Grupo, Categoria
from noticias.models import Noticia
from votacao.models import Voto, ResultadoVotacao


def home(request):
    """Home page with dashboard overview"""
    
    # Get statistics
    total_grupos = Grupo.objects.filter(ativo=True).count()
    
    # Get categories and their group counts
    categorias_stats = []
    for categoria in Categoria.objects.filter(ativa=True).order_by('ordem'):
        count = Grupo.objects.filter(ativo=True, categoria=categoria).count()
        categorias_stats.append({
            'categoria': categoria,
            'count': count
        })
    
    # For backward compatibility with templates
    grupos_escola_samba = 0
    grupos_bloco_rua = 0
    for stat in categorias_stats:
        if stat['categoria'].codigo == 'escola_samba':
            grupos_escola_samba = stat['count']
        elif stat['categoria'].codigo == 'bloco_rua':
            grupos_bloco_rua = stat['count']
    
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
        'categorias_stats': categorias_stats,
        'total_votos': total_votos,
        'noticias_destaque': noticias_destaque,
        'noticias_recentes': noticias_recentes,
        'top_grupos': top_grupos,
        'grupos_destaque': grupos_destaque,
    }
    
    return render(request, 'core/home.html', context)
