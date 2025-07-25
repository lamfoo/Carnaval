import time
import uuid
import random
import string
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import logging

# Importar SDK oficial M-Pesa
from portalsdk import APIContext, APIMethodType, APIRequest

logger = logging.getLogger(__name__)


class MPesaService:
    """Serviço para integração com M-Pesa usando SDK oficial"""
    
    def __init__(self):
        self.api_key = settings.MPESA_API_KEY
        self.public_key = settings.MPESA_PUBLIC_KEY
        self.service_provider_code = settings.MPESA_SERVICE_PROVIDER_CODE
        self.address = 'api.sandbox.vm.co.mz'
        self.port = 18352
        self.path = '/ipg/v1x/c2bPayment/singleStage/'
    
    def generate_transaction_reference(self):
        """Gera referência única para transação (sempre diferente)"""
        timestamp = str(int(time.time()))
        random_letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        random_numbers = ''.join(random.choices(string.digits, k=3))
        return f"CV{timestamp[-4:]}{random_letters}{random_numbers}"
    
    def generate_third_party_reference(self):
        """Gera referência única de terceira parte (sempre diferente)"""
        timestamp = str(int(time.time()))
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{timestamp[-3:]}{random_part}"
    
    def validate_phone_number(self, phone_number):
        """Valida e formata número de telefone moçambicano"""
        # Remove espaços e caracteres especiais
        phone = ''.join(filter(str.isdigit, phone_number))
        
        # Verifica se tem pelo menos 9 dígitos
        if len(phone) < 9:
            return None
        
        # Se começar com 258, está no formato internacional
        if phone.startswith('258'):
            if len(phone) == 12:
                return phone
        
        # Se começar com 8 ou 2, adiciona 258
        if phone.startswith(('8', '2')) and len(phone) == 9:
            return f"258{phone}"
        
        # Se começar com 0, remove o 0 e adiciona 258
        if phone.startswith('0') and len(phone) == 10:
            return f"258{phone[1:]}"
        
        return None
    
    def initiate_payment(self, phone_number, amount, grupo_id, categoria, device_id, ip_address):
        """Inicia pagamento C2B com M-Pesa usando SDK oficial"""
        from .models import Payment
        
        # Valida número de telefone
        formatted_phone = self.validate_phone_number(phone_number)
        if not formatted_phone:
            return {
                'success': False,
                'error': 'Número de telefone inválido. Use formato: 258843330333 ou 843330333'
            }
        
        # Gera referências únicas (sempre diferentes)
        transaction_ref = self.generate_transaction_reference()
        third_party_ref = self.generate_third_party_reference()
        
        logger.info(f"Gerando pagamento M-Pesa - TransRef: {transaction_ref}, ThirdPartyRef: {third_party_ref}")
        
        try:
            # Cria registro de pagamento
            from grupos.models import Grupo
            grupo = Grupo.objects.get(id=grupo_id)
            
            payment = Payment.objects.create(
                transaction_reference=transaction_ref,
                third_party_reference=third_party_ref,
                customer_msisdn=formatted_phone,
                amount=amount,
                grupo=grupo,
                categoria=categoria,
                device_id=device_id,
                ip_address=ip_address,
                expires_at=timezone.now() + timedelta(seconds=settings.PAYMENT_TIMEOUT),
                status='processing'
            )
            
            # Configurar contexto da API M-Pesa
            api_context = APIContext()
            api_context.api_key = self.api_key
            api_context.public_key = self.public_key
            api_context.ssl = True
            api_context.method_type = APIMethodType.POST
            api_context.address = self.address
            api_context.port = self.port
            api_context.path = self.path
            
            # Adicionar headers
            api_context.add_header('Origin', '*')
            
            # Adicionar parâmetros únicos
            api_context.add_parameter('input_TransactionReference', transaction_ref)
            api_context.add_parameter('input_CustomerMSISDN', formatted_phone)
            api_context.add_parameter('input_Amount', str(amount))
            api_context.add_parameter('input_ThirdPartyReference', third_party_ref)
            api_context.add_parameter('input_ServiceProviderCode', self.service_provider_code)
            
            logger.info(f"Chamando M-Pesa API: {transaction_ref} para {formatted_phone}")
            
            # Executar requisição
            api_request = APIRequest(api_context)
            result = api_request.execute()
            
            if result is None:
                payment.status = 'failed'
                payment.response_desc = 'Connection error to M-Pesa API'
                payment.save()
                return {
                    'success': False,
                    'error': 'Erro de conexão com M-Pesa. Tente novamente.'
                }
            
            logger.info(f"Resposta M-Pesa: Status {result.status_code}, Body: {result.body}")
            
            # Processar resposta
            if result.status_code in [200, 201]:
                response_body = result.body
                
                # Atualizar dados do pagamento
                payment.conversation_id = response_body.get('output_ConversationID', '')
                payment.transaction_id = response_body.get('output_TransactionID', '')
                payment.response_code = response_body.get('output_ResponseCode', '')
                payment.response_desc = response_body.get('output_ResponseDesc', '')
                
                response_code = response_body.get('output_ResponseCode', '')
                
                if response_code == 'INS-0':
                    payment.status = 'completed'
                    payment.save()
                    
                    logger.info(f"Pagamento bem-sucedido: {transaction_ref}")
                    
                    return {
                        'success': True,
                        'payment_id': payment.id,
                        'transaction_reference': transaction_ref,
                        'conversation_id': payment.conversation_id,
                        'message': 'Pagamento processado com sucesso!'
                    }
                elif response_code == 'INS-9':
                    # Timeout específico do M-Pesa
                    payment.status = 'timeout'
                    payment.save()
                    
                    logger.warning(f"Timeout M-Pesa (INS-9): {transaction_ref}")
                    
                    return {
                        'success': False,
                        'error': 'Tempo limite esgotado. Por favor, insira o PIN M-Pesa mais rapidamente na próxima tentativa.',
                        'timeout': True
                    }
                else:
                    payment.status = 'failed'
                    payment.save()
                    
                    error_msg = response_body.get('output_ResponseDesc', 'Erro desconhecido')
                    logger.error(f"Pagamento falhou ({response_code}): {error_msg}")
                    
                    return {
                        'success': False,
                        'error': f"Pagamento falhou: {error_msg}"
                    }
            elif result.status_code == 408:
                # Timeout - usuário não inseriu PIN a tempo
                payment.status = 'timeout'
                payment.response_desc = 'Timeout - PIN não inserido a tempo'
                payment.save()
                
                logger.warning(f"Timeout no pagamento: {transaction_ref}")
                
                return {
                    'success': False,
                    'error': 'Tempo esgotado. O usuário deve inserir o PIN M-Pesa em até 2 minutos. Tente novamente.',
                    'timeout': True
                }
            else:
                payment.status = 'failed'
                payment.response_desc = f'HTTP {result.status_code}'
                payment.save()
                
                logger.error(f"Erro HTTP: {result.status_code}")
                
                # Mensagens específicas para códigos de erro comuns
                error_messages = {
                    400: 'Dados inválidos enviados para M-Pesa',
                    401: 'Erro de autenticação M-Pesa',
                    403: 'Acesso negado pelo M-Pesa',
                    404: 'Serviço M-Pesa não encontrado',
                    429: 'Muitas tentativas. Aguarde alguns minutos',
                    500: 'Erro interno do servidor M-Pesa',
                    502: 'Gateway M-Pesa indisponível',
                    503: 'Serviço M-Pesa temporariamente indisponível'
                }
                
                error_msg = error_messages.get(result.status_code, f'Erro na comunicação com M-Pesa (HTTP {result.status_code})')
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Exceção ao processar pagamento: {str(e)}")
            return {
                'success': False,
                'error': 'Erro interno ao processar pagamento'
            }
    
    def check_payment_status(self, payment_id):
        """Verifica status de um pagamento"""
        from .models import Payment
        
        try:
            payment = Payment.objects.get(id=payment_id)
            
            if payment.is_expired and payment.status in ['pending', 'processing']:
                payment.status = 'timeout'
                payment.save()
            
            return {
                'status': payment.status,
                'is_successful': payment.is_successful,
                'response_desc': payment.response_desc,
                'expires_at': payment.expires_at.isoformat() if payment.expires_at else None
            }
            
        except Payment.DoesNotExist:
            return {
                'status': 'not_found',
                'is_successful': False,
                'response_desc': 'Pagamento não encontrado'
            }