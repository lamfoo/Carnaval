#!/usr/bin/env python
"""
Script para configurar demonstração do sistema sem M-Pesa real
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carnaval_beira.settings')
django.setup()

def setup_demo_environment():
    """Configura ambiente de demonstração"""
    
    print("🎭 Configurando Demonstração do Carnaval da Beira...")
    
    # Configurar variáveis de ambiente para demo
    demo_env = {
        'MPESA_PUBLIC_KEY': 'demo_public_key',
        'MPESA_API_KEY': 'demo_api_key',
        'MPESA_SERVICE_PROVIDER_CODE': '171717'
    }
    
    for key, value in demo_env.items():
        os.environ[key] = value
        
    print(f"✅ Variáveis de ambiente configuradas:")
    for key in demo_env.keys():
        print(f"   - {key}: {'*' * 20}")
    
    print("\n📝 AVISO IMPORTANTE:")
    print("   Este é um ambiente de DEMONSTRAÇÃO!")
    print("   As transações M-Pesa NÃO serão processadas realmente.")
    print("   Para produção, configure as credenciais reais no arquivo .env")
    
    print("\n🚀 Para iniciar a demonstração:")
    print("   1. python manage.py runserver")
    print("   2. Acesse: http://localhost:8000/")
    print("   3. Teste a votação com qualquer número de telefone")
    
    return True

if __name__ == '__main__':
    setup_demo_environment()