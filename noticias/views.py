from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Noticia


def lista_noticias(request):
    """List all published news with search and pagination"""
    
    # Get search parameter
    search = request.GET.get('search', '').strip()
    
    # Base queryset - only published news
    noticias = Noticia.objects.filter(publicada=True)
    
    # Apply search filter
    if search:
        noticias = noticias.filter(
            Q(titulo__icontains=search) |
            Q(conteudo__icontains=search) |
            Q(autor__icontains=search)
        )
    
    # Order by publication date (featured first, then by date)
    noticias = noticias.order_by('-destaque', '-data_publicacao')
    
    # Pagination
    paginator = Paginator(noticias, 10)  # 10 news per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get featured news for the sidebar (if not searching)
    noticias_destaque = None
    if not search:
        noticias_destaque = Noticia.objects.filter(
            publicada=True,
            destaque=True
        ).order_by('-data_publicacao')[:5]
    
    # Get recent news for sidebar
    noticias_recentes = Noticia.objects.filter(
        publicada=True
    ).order_by('-data_publicacao')[:8]
    
    context = {
        'page_obj': page_obj,
        'noticias': page_obj.object_list,
        'search_query': search,
        'noticias_destaque': noticias_destaque,
        'noticias_recentes': noticias_recentes,
        'total_noticias': noticias.count(),
    }
    
    return render(request, 'noticias/lista.html', context)


def detalhe_noticia(request, noticia_id):
    """Show detailed view of a specific news article"""
    
    noticia = get_object_or_404(
        Noticia.objects.filter(publicada=True),
        id=noticia_id
    )
    
    # Get related news (same time period or recent)
    noticias_relacionadas = Noticia.objects.filter(
        publicada=True
    ).exclude(
        id=noticia.id
    ).order_by('-data_publicacao')[:6]
    
    # Get recent featured news
    noticias_destaque = Noticia.objects.filter(
        publicada=True,
        destaque=True
    ).exclude(
        id=noticia.id
    ).order_by('-data_publicacao')[:4]
    
    context = {
        'noticia': noticia,
        'noticias_relacionadas': noticias_relacionadas,
        'noticias_destaque': noticias_destaque,
    }
    
    return render(request, 'noticias/detalhe.html', context)
