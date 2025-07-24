import requests
import json
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class MPesaService:
    """Serviço para integração com M-Pesa API"""
    
    def __init__(self):
        self.api_url = settings.MPESA_API_URL
        self.auth_url = settings.MPESA_AUTH_URL
        self.c2b_url = settings.MPESA_C2B_URL
        self.public_key = settings.MPESA_PUBLIC_KEY
        self.api_key = settings.MPESA_API_KEY
        self.service_provider_code = settings.MPESA_SERVICE_PROVIDER_CODE
        self.origin = settings.MPESA_ORIGIN
    
    def get_access_token(self):
        """Obtém token de acesso do M-Pesa"""
        # Demo mode check
        if self.api_key == 'demo_api_key':
            return 'demo_access_token_12345'
            
        cache_key = 'mpesa_access_token'
        token = cache.get(cache_key)
        
        if token:
            return token
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': self.origin,
            }
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(
                self.auth_url,
                headers=headers,
                json=data,
                auth=(self.api_key, ''),
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                
                # Cache token por 90% do tempo de expiração
                cache.set(cache_key, access_token, expires_in * 0.9)
                return access_token
            else:
                logger.error(f"Erro ao obter token M-Pesa: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exceção ao obter token M-Pesa: {str(e)}")
            return None
    
    def generate_transaction_reference(self):
        """Gera referência única para transação"""
        timestamp = str(int(time.time()))
        random_part = str(uuid.uuid4())[:8]
        return f"CV{timestamp[-6:]}{random_part.upper()}"
    
    def generate_third_party_reference(self):
        """Gera referência única de terceira parte"""
        return str(uuid.uuid4()).replace('-', '')[:20].upper()
    
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
        """Inicia pagamento C2B com M-Pesa"""
        from .models import Payment
        
        # Valida número de telefone
        formatted_phone = self.validate_phone_number(phone_number)
        if not formatted_phone:
            return {
                'success': False,
                'error': 'Número de telefone inválido. Use formato: 258843330333 ou 843330333'
            }
        
        # Obtém token de acesso
        access_token = self.get_access_token()
        if not access_token:
            return {
                'success': False,
                'error': 'Erro interno: não foi possível obter token de autenticação'
            }
        
        # Gera referências únicas
        transaction_ref = self.generate_transaction_reference()
        third_party_ref = self.generate_third_party_reference()
        
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
            
            # Prepara dados para API M-Pesa
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Origin': self.origin,
            }
            
            payload = {
                'input_TransactionReference': transaction_ref,
                'input_CustomerMSISDN': formatted_phone,
                'input_Amount': str(amount),
                'input_ThirdPartyReference': third_party_ref,
                'input_ServiceProviderCode': self.service_provider_code
            }
            
            logger.info(f"Iniciando pagamento M-Pesa: {payload}")
            
            # Demo mode - simulate successful payment
            if self.api_key == 'demo_api_key':
                import random
                import string
                
                # Simulate M-Pesa response
                fake_conversation_id = f"AG_{''.join(random.choices(string.ascii_uppercase + string.digits, k=20))}"
                fake_transaction_id = f"{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                
                payment.conversation_id = fake_conversation_id
                payment.transaction_id = fake_transaction_id
                payment.response_code = 'INS-0'
                payment.response_desc = 'Request processed successfully (DEMO MODE)'
                payment.status = 'completed'
                payment.save()
                
                logger.info(f"DEMO MODE: Pagamento simulado com sucesso para {formatted_phone}")
                
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'transaction_reference': transaction_ref,
                    'conversation_id': payment.conversation_id,
                    'message': 'Pagamento processado com sucesso! (MODO DEMONSTRAÇÃO)'
                }
            
            # Real M-Pesa API call
            response = requests.post(
                self.c2b_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"Resposta M-Pesa: {response.status_code} - {response.text}")
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                
                # Atualiza dados do pagamento
                payment.conversation_id = response_data.get('output_ConversationID')
                payment.transaction_id = response_data.get('output_TransactionID')
                payment.response_code = response_data.get('output_ResponseCode')
                payment.response_desc = response_data.get('output_ResponseDesc')
                
                if response_data.get('output_ResponseCode') == 'INS-0':
                    payment.status = 'completed'
                    payment.save()
                    
                    return {
                        'success': True,
                        'payment_id': payment.id,
                        'transaction_reference': transaction_ref,
                        'conversation_id': payment.conversation_id,
                        'message': 'Pagamento processado com sucesso! Verifique seu telefone para confirmar.'
                    }
                else:
                    payment.status = 'failed'
                    payment.save()
                    
                    return {
                        'success': False,
                        'error': f"Pagamento falhou: {response_data.get('output_ResponseDesc', 'Erro desconhecido')}"
                    }
            else:
                payment.status = 'failed'
                payment.save()
                
                return {
                    'success': False,
                    'error': f'Erro na comunicação com M-Pesa: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {str(e)}")
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