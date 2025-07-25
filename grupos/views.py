from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.core.paginator import Paginator
from .models import Grupo, Categoria


def lista_grupos(request):
    """List all active groups with filtering by category"""
    
    # Get filter parameters
    categoria = request.GET.get('categoria', 'all')
    search = request.GET.get('search', '').strip()
    
    # Base queryset
    grupos = Grupo.objects.filter(ativo=True).select_related()
    
    # Apply category filter
    if categoria and categoria != 'all':
        grupos = grupos.filter(categoria=categoria)
    
    # Apply search filter
    if search:
        grupos = grupos.filter(
            Q(nome_grupo__icontains=search) |
            Q(descricao__icontains=search) |
            Q(representante__icontains=search)
        )
    
    # Order by name
    grupos = grupos.order_by('nome_grupo')
    
    # Annotate with vote count
    grupos = grupos.annotate(total_votos=Count('votos'))
    
    # Pagination
    paginator = Paginator(grupos, 12)  # 12 groups per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics for the page
    total_grupos = grupos.count()
    grupos_escola_samba = grupos.filter(categoria='escola_samba').count()
    grupos_bloco_rua = grupos.filter(categoria='bloco_rua').count()
    
    context = {
        'page_obj': page_obj,
        'grupos': page_obj.object_list,
        'categoria_atual': categoria,
        'search_query': search,
        'total_grupos': total_grupos,
        'grupos_escola_samba': grupos_escola_samba,
        'grupos_bloco_rua': grupos_bloco_rua,
        'categorias': Categoria.objects.filter(ativa=True).order_by('ordem'),
    }
    
    return render(request, 'grupos/lista.html', context)


def detalhe_grupo(request, grupo_id):
    """Show detailed information about a specific group"""
    
    grupo = get_object_or_404(
        Grupo.objects.select_related().annotate(
            total_votos=Count('votos')
        ),
        id=grupo_id,
        ativo=True
    )
    
    # Get related groups from the same category
    grupos_relacionados = Grupo.objects.filter(
        categoria=grupo.categoria,
        ativo=True
    ).exclude(
        id=grupo.id
    ).annotate(
        total_votos=Count('votos')
    ).order_by('-total_votos')[:4]
    
    # Check if user has already voted for this group's category
    user_voted = False
    if request.session.get('device_id'):
        from votacao.models import Voto
        user_voted = Voto.objects.filter(
            device_id=request.session['device_id'],
            categoria=grupo.categoria
        ).exists()
    
    context = {
        'grupo': grupo,
        'grupos_relacionados': grupos_relacionados,
        'user_voted': user_voted,
    }
    
    return render(request, 'grupos/detalhe.html', context)
