from django.db import models
from django.utils import timezone
from grupos.models import Grupo
import hashlib


def generate_device_id(ip_address, user_agent):
    """Generate a secure device ID based on IP and user agent"""
    combined = f"{ip_address}:{user_agent}"
    return hashlib.sha256(combined.encode()).hexdigest()


class Voto(models.Model):
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        verbose_name="Grupo",
        related_name="votos"
    )
    categoria = models.ForeignKey(
        'grupos.Categoria',
        on_delete=models.CASCADE,
        verbose_name="Categoria"
    )
    device_id = models.CharField(
        max_length=64,
        verbose_name="ID do Dispositivo",
        help_text="Hash SHA-256 do IP + User-Agent"
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="Endereço IP",
        help_text="IP do votante (para auditoria)"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data/Hora do Voto"
    )
    
    class Meta:
        verbose_name = "Voto"
        verbose_name_plural = "Votos"
        ordering = ['-timestamp']
        # Unique constraint: one vote per device per category
        unique_together = [['device_id', 'categoria']]
        indexes = [
            models.Index(fields=['categoria', 'grupo']),
            models.Index(fields=['device_id']),
            models.Index(fields=['timestamp']),
        ]
        
    def __str__(self):
        return f"Voto para {self.grupo.nome_grupo} - {self.get_categoria_display()}"
        
    def save(self, *args, **kwargs):
        # Ensure categoria matches grupo's categoria
        if self.grupo:
            self.categoria = self.grupo.categoria
        super().save(*args, **kwargs)


class ResultadoVotacao(models.Model):
    """Model to store voting results summary"""
    categoria = models.ForeignKey(
        'grupos.Categoria',
        on_delete=models.CASCADE,
        unique=True,
        verbose_name="Categoria"
    )
    total_votos = models.PositiveIntegerField(
        default=0,
        verbose_name="Total de Votos"
    )
    ultimo_update = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização"
    )
    
    class Meta:
        verbose_name = "Resultado da Votação"
        verbose_name_plural = "Resultados da Votação"
        
    def __str__(self):
        return f"Resultado - {self.get_categoria_display()}"
        
    @classmethod
    def update_results(cls, categoria):
        """Update voting results for a specific category"""
        total = Voto.objects.filter(categoria=categoria).count()
        result, created = cls.objects.get_or_create(
            categoria=categoria,
            defaults={'total_votos': total}
        )
        if not created:
            result.total_votos = total
            result.save()
        return result


class VotingSession(models.Model):
    """Model to track voting sessions and prevent abuse"""
    session_key = models.CharField(
        max_length=40,
        unique=True,
        verbose_name="Chave da Sessão"
    )
    device_id = models.CharField(
        max_length=64,
        verbose_name="ID do Dispositivo"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Criado em"
    )
    votes_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantidade de Votos"
    )
    
    class Meta:
        verbose_name = "Sessão de Votação"
        verbose_name_plural = "Sessões de Votação"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Sessão {self.session_key[:8]}... - {self.votes_count} votos"


class Payment(models.Model):
    """Modelo para rastrear pagamentos de votos"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('timeout', 'Timeout'),
    ]
    
    # Dados do pagamento
    transaction_reference = models.CharField(max_length=50, unique=True)
    third_party_reference = models.CharField(max_length=50, unique=True)
    customer_msisdn = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Dados da resposta M-Pesa
    conversation_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    response_code = models.CharField(max_length=20, blank=True, null=True)
    response_desc = models.CharField(max_length=200, blank=True, null=True)
    
    # Dados do voto associado
    grupo = models.ForeignKey('grupos.Grupo', on_delete=models.CASCADE)
    categoria = models.CharField(max_length=20, choices=[
        ('escola_samba', 'Escola de Samba'),
        ('bloco_rua', 'Bloco de Rua'),
    ])
    device_id = models.CharField(max_length=64)
    ip_address = models.GenericIPAddressField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_reference']),
            models.Index(fields=['conversation_id']),
            models.Index(fields=['device_id', 'categoria']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Pagamento {self.transaction_reference} - {self.get_status_display()}"
    
    @property
    def is_expired(self):
        """Verifica se o pagamento expirou"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @property
    def is_successful(self):
        """Verifica se o pagamento foi bem-sucedido"""
        return self.status == 'completed' and self.response_code == 'INS-0'
