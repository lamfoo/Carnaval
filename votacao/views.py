from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count, Q
from django.db import transaction, IntegrityError
from django_ratelimit.decorators import ratelimit
from grupos.models import Grupo
from .models import Voto, ResultadoVotacao, VotingSession, generate_device_id
import hashlib


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_or_create_device_id(request):
    """Get or create device ID for the user"""
    if 'device_id' not in request.session:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_id = generate_device_id(ip_address, user_agent)
        request.session['device_id'] = device_id
        request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
    
    return request.session['device_id']


@ratelimit(key='ip', rate='10/m', method='GET')
def votar(request):
    """Voting page with group selection"""
    
    # Check if rate limited
    was_limited = getattr(request, 'limited', False)
    if was_limited:
        messages.error(request, 'Muitas tentativas. Tente novamente em alguns minutos.')
        return redirect('core:home')
    
    # Get or create device ID
    device_id = get_or_create_device_id(request)
    
    # Get categories and check voting status
    categorias_info = []
    for categoria_code, categoria_name in Grupo.CATEGORIA_CHOICES:
        # Check if user already voted in this category
        ja_votou = Voto.objects.filter(
            device_id=device_id,
            categoria=categoria_code
        ).exists()
        
        # Get groups for this category
        grupos = Grupo.objects.filter(
            categoria=categoria_code,
            ativo=True
        ).annotate(
            total_votos=Count('votos')
        ).order_by('nome_grupo')
        
        categorias_info.append({
            'codigo': categoria_code,
            'nome': categoria_name,
            'grupos': grupos,
            'ja_votou': ja_votou,
            'total_grupos': grupos.count(),
        })
    
    # Check if user has voted in all categories
    todas_votadas = all(cat['ja_votou'] for cat in categorias_info)
    
    context = {
        'categorias_info': categorias_info,
        'todas_votadas': todas_votadas,
        'device_id': device_id,
    }
    
    return render(request, 'votacao/votar.html', context)


@require_http_methods(["POST"])
@csrf_protect
@ratelimit(key='ip', rate='5/m', method='POST')
@transaction.atomic
def processar_voto(request):
    """Process a vote submission"""
    
    # Check if rate limited
    was_limited = getattr(request, 'limited', False)
    if was_limited:
        messages.error(request, 'Muitas tentativas de votação. Aguarde alguns minutos.')
        return redirect('votacao:votar')
    
    # Get form data
    grupo_id = request.POST.get('grupo_id')
    categoria = request.POST.get('categoria')
    
    if not grupo_id or not categoria:
        messages.error(request, 'Dados de votação inválidos.')
        return redirect('votacao:votar')
    
    try:
        # Get group and validate category
        grupo = get_object_or_404(Grupo, id=grupo_id, ativo=True)
        if grupo.categoria != categoria:
            messages.error(request, 'Categoria inválida para o grupo selecionado.')
            return redirect('votacao:votar')
        
        # Get or create device ID
        device_id = get_or_create_device_id(request)
        ip_address = get_client_ip(request)
        
        # Check if user already voted in this category
        existing_vote = Voto.objects.filter(
            device_id=device_id,
            categoria=categoria
        ).exists()
        
        if existing_vote:
            messages.warning(request, f'Você já votou na categoria {grupo.get_categoria_display()}.')
            return redirect('votacao:votar')
        
        # Create the vote
        voto = Voto.objects.create(
            grupo=grupo,
            categoria=categoria,
            device_id=device_id,
            ip_address=ip_address
        )
        
        # Update voting session
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        voting_session, created = VotingSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                'device_id': device_id,
                'votes_count': 1
            }
        )
        
        if not created:
            voting_session.votes_count += 1
            voting_session.save()
        
        # Update results cache
        ResultadoVotacao.update_results(categoria)
        
        messages.success(
            request, 
            f'Seu voto para "{grupo.nome_grupo}" na categoria {grupo.get_categoria_display()} foi registrado com sucesso!'
        )
        
    except IntegrityError:
        messages.error(request, 'Erro ao processar o voto. Você já pode ter votado nesta categoria.')
        
    except Exception as e:
        messages.error(request, 'Erro interno. Tente novamente mais tarde.')
        
    return redirect('votacao:votar')


def resultados(request):
    """Display voting results"""
    
    # Get results by category
    resultados_por_categoria = {}
    
    for categoria_code, categoria_name in Grupo.CATEGORIA_CHOICES:
        # Get groups with vote counts
        grupos_com_votos = Grupo.objects.filter(
            categoria=categoria_code,
            ativo=True
        ).annotate(
            total_votos=Count('votos')
        ).order_by('-total_votos', 'nome_grupo')
        
        # Calculate total votes for this category
        total_votos_categoria = sum(grupo.total_votos for grupo in grupos_com_votos)
        
        # Add percentage calculation
        for grupo in grupos_com_votos:
            if total_votos_categoria > 0:
                grupo.porcentagem = (grupo.total_votos / total_votos_categoria) * 100
            else:
                grupo.porcentagem = 0
        
        # Calculate average votes per group
        total_grupos = grupos_com_votos.count()
        media_votos = (total_votos_categoria / total_grupos) if total_grupos > 0 else 0
        
        resultados_por_categoria[categoria_code] = {
            'nome': categoria_name,
            'grupos': grupos_com_votos,
            'total_votos': total_votos_categoria,
            'total_grupos': total_grupos,
            'media_votos': media_votos,
        }
    
    # Overall statistics
    total_votos_geral = Voto.objects.count()
    total_grupos_ativos = Grupo.objects.filter(ativo=True).count()
    
    # Get top 3 overall
    top_grupos_geral = Grupo.objects.filter(ativo=True).annotate(
        total_votos=Count('votos')
    ).order_by('-total_votos')[:3]
    
    context = {
        'resultados_por_categoria': resultados_por_categoria,
        'total_votos_geral': total_votos_geral,
        'total_grupos_ativos': total_grupos_ativos,
        'top_grupos_geral': top_grupos_geral,
    }
    
    return render(request, 'votacao/resultados.html', context)


@require_http_methods(["GET"])
def resultados_json(request):
    """Return results in JSON format for AJAX updates"""
    
    resultados = {}
    
    for categoria_code, categoria_name in Grupo.CATEGORIA_CHOICES:
        grupos_com_votos = Grupo.objects.filter(
            categoria=categoria_code,
            ativo=True
        ).annotate(
            total_votos=Count('votos')
        ).order_by('-total_votos', 'nome_grupo')
        
        total_votos_categoria = sum(grupo.total_votos for grupo in grupos_com_votos)
        
        resultados[categoria_code] = {
            'nome': categoria_name,
            'total_votos': total_votos_categoria,
            'grupos': [
                {
                    'id': grupo.id,
                    'nome': grupo.nome_grupo,
                    'votos': grupo.total_votos,
                    'porcentagem': (grupo.total_votos / total_votos_categoria * 100) if total_votos_categoria > 0 else 0
                }
                for grupo in grupos_com_votos
            ]
        }
    
    return JsonResponse(resultados)


def verificar_voto(request):
    """Check if user has already voted in categories"""
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    device_id = get_or_create_device_id(request)
    
    votos_existentes = {}
    for categoria_code, categoria_name in Grupo.CATEGORIA_CHOICES:
        voto = Voto.objects.filter(
            device_id=device_id,
            categoria=categoria_code
        ).first()
        
        votos_existentes[categoria_code] = {
            'votou': bool(voto),
            'grupo': voto.grupo.nome_grupo if voto else None,
            'timestamp': voto.timestamp.isoformat() if voto else None
        }
    
    return JsonResponse(votos_existentes)
