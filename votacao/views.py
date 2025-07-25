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
import json
import logging
from django.urls import reverse
from django.conf import settings

logger = logging.getLogger(__name__)


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


@ratelimit(key='ip', rate='10/m', method=['GET', 'POST'])
def iniciar_pagamento(request):
    """Inicia processo de pagamento para voto"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    try:
        data = json.loads(request.body)
        phone_number = data.get('phone_number', '').strip()
        grupo_id = data.get('grupo_id')
        categoria = data.get('categoria')
        
        if not all([phone_number, grupo_id, categoria]):
            return JsonResponse({
                'success': False, 
                'error': 'Dados obrigatórios não fornecidos'
            })
        
        # Verifica se o grupo existe
        try:
            from grupos.models import Grupo
            grupo = Grupo.objects.get(id=grupo_id, ativo=True)
        except Grupo.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Grupo não encontrado'
            })
        
        # Verifica se categoria é válida
        if categoria not in ['escola_samba', 'bloco_rua']:
            return JsonResponse({
                'success': False, 
                'error': 'Categoria inválida'
            })
        
        # Verifica se o grupo está na categoria correta
        if grupo.categoria != categoria:
            return JsonResponse({
                'success': False, 
                'error': 'Grupo não pertence à categoria selecionada'
            })
        
        # Obtém device_id e IP
        device_id = get_or_create_device_id(request)
        ip_address = get_client_ip(request)
        
        # Verifica se já votou nesta categoria
        if Voto.objects.filter(device_id=device_id, categoria=categoria).exists():
            return JsonResponse({
                'success': False, 
                'error': 'Você já votou nesta categoria'
            })
        
        # Verifica se já tem pagamento pendente
        from .models import Payment
        existing_payment = Payment.objects.filter(
            device_id=device_id,
            categoria=categoria,
            status__in=['pending', 'processing']
        ).first()
        
        if existing_payment and not existing_payment.is_expired:
            return JsonResponse({
                'success': False, 
                'error': 'Já existe um pagamento em andamento para esta categoria'
            })
        
        # Inicia pagamento M-Pesa
        from .services import MPesaService
        mpesa_service = MPesaService()
        
        result = mpesa_service.initiate_payment(
            phone_number=phone_number,
            amount=settings.VOTE_PRICE,
            grupo_id=grupo_id,
            categoria=categoria,
            device_id=device_id,
            ip_address=ip_address
        )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Dados JSON inválidos'
        })
    except Exception as e:
        logger.error(f"Erro ao iniciar pagamento: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': 'Erro interno do servidor'
        })


@ratelimit(key='ip', rate='30/m', method=['GET'])
def verificar_pagamento(request):
    """Verifica status de pagamento"""
    payment_id = request.GET.get('payment_id')
    
    if not payment_id:
        return JsonResponse({
            'success': False, 
            'error': 'ID do pagamento não fornecido'
        })
    
    try:
        from .services import MPesaService
        mpesa_service = MPesaService()
        
        result = mpesa_service.check_payment_status(payment_id)
        
        # Se pagamento foi bem-sucedido, processa voto
        if result.get('is_successful'):
            device_id = get_or_create_device_id(request)
            
            # Verifica se voto já foi processado
            from .models import Payment
            payment = Payment.objects.get(id=payment_id)
            
            logger.info(f"Pagamento {payment_id} bem-sucedido, verificando voto para device {device_id}, categoria {payment.categoria}")
            
            # Verifica se voto já foi processado
            existing_vote = Voto.objects.filter(device_id=device_id, categoria=payment.categoria).first()
            
            if not existing_vote:
                logger.info(f"Processando voto para pagamento {payment_id}")
                # Processa o voto
                voto_result = _processar_voto_apos_pagamento(payment, request)
                result.update(voto_result)
            else:
                logger.info(f"Voto já processado para device {device_id}, categoria {payment.categoria}")
                # Voto já foi processado anteriormente
                result.update({
                    'vote_processed': True,
                    'grupo_nome': payment.grupo.nome_grupo,
                    'categoria': payment.get_categoria_display(),
                    'redirect_url': reverse('votacao:resultados')
                })
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Erro ao verificar pagamento: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': 'Erro interno do servidor'
        })


def _processar_voto_apos_pagamento(payment, request):
    """Processa voto após confirmação de pagamento"""
    try:
        device_id = get_or_create_device_id(request)
        ip_address = get_client_ip(request)
        
        # Cria o voto
        voto = Voto.objects.create(
            grupo=payment.grupo,
            categoria=payment.categoria,
            device_id=device_id,
            ip_address=ip_address
        )
        
        # Atualiza resultados
        ResultadoVotacao.update_results(payment.categoria)
        
        # Atualiza sessão de votação
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        voting_session, created = VotingSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                'device_id': device_id,
                'votes_count': 0
            }
        )
        voting_session.votes_count += 1
        voting_session.save()
        
        return {
            'vote_processed': True,
            'grupo_nome': payment.grupo.nome_grupo,
            'categoria': payment.get_categoria_display(),
            'redirect_url': reverse('votacao:resultados')
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar voto após pagamento: {str(e)}")
        return {
            'vote_processed': False,
            'error': 'Erro ao processar voto'
        }


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
    from grupos.models import Categoria
    for categoria in Categoria.objects.filter(ativa=True).order_by('ordem'):
        # Check if user already voted in this category
        ja_votou = Voto.objects.filter(
            device_id=device_id,
            categoria=categoria
        ).exists()
        
        # Get groups for this category
        grupos = Grupo.objects.filter(
            categoria=categoria,
            ativo=True
        ).annotate(
            total_votos=Count('votos')
        ).order_by('nome_grupo')
        
        categorias_info.append({
            'codigo': categoria.codigo,
            'nome': categoria.nome,
            'categoria_obj': categoria,
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
    
    for categoria in Categoria.objects.filter(ativa=True).order_by('ordem'):
        # Get groups with vote counts
        grupos_com_votos = Grupo.objects.filter(
            categoria=categoria,
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
        
        resultados_por_categoria[categoria.codigo] = {
            'nome': categoria.nome,
            'categoria_obj': categoria,
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
    
    for categoria in Categoria.objects.filter(ativa=True).order_by('ordem'):
        grupos_com_votos = Grupo.objects.filter(
            categoria=categoria,
            ativo=True
        ).annotate(
            total_votos=Count('votos')
        ).order_by('-total_votos', 'nome_grupo')
        
        total_votos_categoria = sum(grupo.total_votos for grupo in grupos_com_votos)
        
        resultados[categoria.codigo] = {
            'nome': categoria.nome,
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
    for categoria in Categoria.objects.filter(ativa=True).order_by('ordem'):
        voto = Voto.objects.filter(
            device_id=device_id,
            categoria=categoria
        ).first()
        
        votos_existentes[categoria.codigo] = {
            'votou': bool(voto),
            'grupo': voto.grupo.nome_grupo if voto else None,
            'timestamp': voto.timestamp.isoformat() if voto else None
        }
    
    return JsonResponse(votos_existentes)
