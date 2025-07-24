# 💳 Integração M-Pesa - Carnaval da Beira

## Visão Geral

Sistema de votação com pagamento integrado via M-Pesa API. Cada voto custa **10 MZN** e é processado através da API C2B (Customer-to-Business) do M-Pesa.

## 🔧 Configuração

### 1. Credenciais M-Pesa

Obtenha suas credenciais em: https://developer.mpesa.vm.co.mz

```bash
# .env
MPESA_PUBLIC_KEY=sua_chave_publica_aqui
MPESA_API_KEY=sua_chave_api_aqui
MPESA_SERVICE_PROVIDER_CODE=171717
```

### 2. URLs da API

- **Sandbox**: `https://api.sandbox.vm.co.mz:18352`
- **Produção**: `https://api.vm.co.mz:18352`

## 🔄 Fluxo de Pagamento

### Sequência de Eventos

1. **Seleção do Grupo**
   - Usuário clica em "Selecionar para Voto"
   - Modal de pagamento é exibido

2. **Entrada de Dados**
   - Usuário insere número de telefone M-Pesa
   - Sistema valida formato (258xxxxxxxxx)

3. **Processamento M-Pesa**
   - Sistema gera referências únicas
   - Chama API C2B do M-Pesa
   - Cria registro de pagamento

4. **Confirmação USSD**
   - Usuário recebe push USSD no telefone
   - Insere PIN M-Pesa para confirmar

5. **Verificação e Voto**
   - Sistema monitora status do pagamento
   - Após confirmação, registra o voto automaticamente

### Códigos de Status

| Status | Descrição |
|--------|-----------|
| `pending` | Aguardando processamento |
| `processing` | Em processamento no M-Pesa |
| `completed` | Pagamento confirmado |
| `failed` | Pagamento rejeitado |
| `timeout` | Tempo limite esgotado (5 min) |

## 📱 Interface do Usuário

### Modal de Pagamento

```javascript
// Estrutura do modal
Modal Steps:
1. Entrada do telefone (payment-step-1)
2. Processamento (payment-step-2) 
3. Sucesso (payment-step-3)
4. Erro (payment-step-4)
```

### Validação de Telefone

Formatos aceitos:
- `258843330333` (formato internacional)
- `843330333` (formato local)
- `0843330333` (com zero inicial)

## 🔐 Segurança

### Transações Únicas
- **Transaction Reference**: `CV{timestamp}{random}`
- **Third Party Reference**: UUID único
- **Device ID**: Hash SHA-256 do IP + User-Agent

### Validações
- ✅ Número de telefone moçambicano
- ✅ Grupo existe e está ativo
- ✅ Usuário não votou na categoria
- ✅ Sem pagamentos pendentes
- ✅ Rate limiting (10 requests/min)

### Logs e Auditoria
- Todas as transações são logadas
- Status detalhado de cada pagamento
- Rastreabilidade completa via admin

## 🛠️ Desenvolvimento

### Modelo Payment

```python
class Payment(models.Model):
    # Dados do pagamento
    transaction_reference = models.CharField(max_length=50, unique=True)
    customer_msisdn = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Resposta M-Pesa
    conversation_id = models.CharField(max_length=100)
    response_code = models.CharField(max_length=20)
    
    # Dados do voto
    grupo = models.ForeignKey('grupos.Grupo')
    categoria = models.CharField(max_length=20)
    device_id = models.CharField(max_length=64)
```

### Service Layer

```python
class MPesaService:
    def initiate_payment(phone, amount, grupo_id, categoria, device_id, ip):
        # Validação + Chamada API + Criação Payment
    
    def check_payment_status(payment_id):
        # Verificação de status + Timeout
```

### Views

- `iniciar_pagamento()`: POST para iniciar transação
- `verificar_pagamento()`: GET para consultar status
- `_processar_voto_apos_pagamento()`: Registra voto após confirmação

## 🧪 Modo Demonstração

Para testar sem credenciais reais:

```bash
python demo_setup.py
python manage.py runserver
```

**Características do Demo:**
- ✅ Simula transações M-Pesa
- ✅ Aceita qualquer número de telefone
- ✅ Sucesso automático em 3 segundos
- ✅ Logs marcados como "DEMO MODE"

## 📊 Monitoramento

### Admin Django

Acesse `/admin/` para monitorar:
- **Payments**: Todas as transações
- **Votos**: Votos registrados
- **Resultados**: Estatísticas em tempo real

### Campos Importantes

- **Transaction Reference**: Rastreamento único
- **Conversation ID**: ID M-Pesa para suporte
- **Response Code**: `INS-0` = sucesso
- **Status**: Estado atual da transação

## ⚠️ Produção

### Checklist de Deploy

- [ ] Credenciais M-Pesa reais configuradas
- [ ] URLs de produção (api.vm.co.mz)
- [ ] SSL/HTTPS habilitado
- [ ] Cache Redis/Memcached
- [ ] Logs centralizados
- [ ] Monitoramento de erros
- [ ] Backup automático do banco

### Códigos de Erro M-Pesa

| Código | Descrição |
|--------|-----------|
| `INS-0` | ✅ Sucesso |
| `INS-1` | ❌ Erro interno |
| `INS-5` | ❌ Cancelado pelo cliente |
| `INS-6` | ❌ Transação falhou |
| `INS-2006` | ❌ Saldo insuficiente |
| `INS-2051` | ❌ MSISDN inválido |

## 🔗 Links Úteis

- [M-Pesa Developer Portal](https://developer.mpesa.vm.co.mz)
- [API Documentation](https://developer.mpesa.vm.co.mz/docs)
- [Sandbox Testing](https://developer.mpesa.vm.co.mz/docs/testing)

---

**🎭 Sistema desenvolvido para o Carnaval da Beira**  
*Integração M-Pesa completa e funcional*