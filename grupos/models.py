from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import os


def grupo_photo_upload_path(instance, filename):
    """Upload path for group photos"""
    return f'grupos/{instance.nome_grupo}/{filename}'


class Categoria(models.Model):
    """Model for dynamic group categories"""
    nome = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nome da Categoria",
        help_text="Nome da categoria (ex: Escola de Samba, Bloco de Rua)"
    )
    codigo = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="Código",
        help_text="Código único para a categoria (ex: escola_samba, bloco_rua)"
    )
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição da categoria"
    )
    icone = models.CharField(
        max_length=50,
        default="bi-people",
        verbose_name="Ícone Bootstrap",
        help_text="Ícone Bootstrap Icons (ex: bi-star, bi-people, bi-music-note)"
    )
    cor_primaria = models.CharField(
        max_length=7,
        default="#FF6B35",
        verbose_name="Cor Primária",
        help_text="Cor primária em hexadecimal (ex: #FF6B35)"
    )
    cor_secundaria = models.CharField(
        max_length=7,
        default="#F7931E",
        verbose_name="Cor Secundária",
        help_text="Cor secundária em hexadecimal (ex: #F7931E)"
    )
    ativa = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Categoria disponível para novos grupos"
    )
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Ordem de exibição (0 = primeiro)"
    )
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['ordem', 'nome']
    
    def __str__(self):
        return self.nome


class Grupo(models.Model):
    
    nome_grupo = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Nome do Grupo",
        help_text="Nome único do grupo carnavalesco"
    )
    representante = models.CharField(
        max_length=100,
        verbose_name="Representante"
    )
    
    # Contact validation - accepts phone numbers and emails
    contato_validator = RegexValidator(
        regex=r'^(\+?55\s?)?\(?([1-9]{2})\)?\s?9?\d{4}-?\d{4}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        message='Contato deve ser um telefone válido (ex: (11) 99999-9999) ou email válido'
    )
    contato = models.CharField(
        max_length=150,
        validators=[contato_validator],
        verbose_name="Contato"
    )
    
    descricao = models.TextField(
        verbose_name="Descrição",
        help_text="Descrição do grupo e sua história"
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        verbose_name="Categoria",
        help_text="Categoria do grupo"
    )
    data_inscricao = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data de Inscrição"
    )
    foto = models.ImageField(
        upload_to=grupo_photo_upload_path,
        blank=True,
        null=True,
        verbose_name="Foto",
        help_text="Foto representativa do grupo"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Grupo ativo para participação"
    )
    
    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        ordering = ['nome_grupo']
        
    def __str__(self):
        return self.nome_grupo
        
    def save(self, *args, **kwargs):
        # Ensure nome_grupo is properly formatted
        self.nome_grupo = self.nome_grupo.strip().title()
        super().save(*args, **kwargs)


class Participante(models.Model):
    """Model for group participants"""
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='participantes',
        verbose_name="Grupo"
    )
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome do Participante"
    )
    funcao = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Função",
        help_text="Função no grupo (ex: Diretor, Mestre-sala, Porta-bandeira)"
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefone",
        help_text="Telefone de contato (opcional)"
    )
    email = models.EmailField(
        blank=True,
        verbose_name="Email",
        help_text="Email de contato (opcional)"
    )
    data_nascimento = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Nascimento",
        help_text="Data de nascimento (opcional)"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Participante ativo no grupo"
    )
    data_adicao = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data de Adição"
    )
    
    class Meta:
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        ordering = ['nome']
        unique_together = ['grupo', 'nome']  # Evita nomes duplicados no mesmo grupo
    
    def __str__(self):
        if self.funcao:
            return f"{self.nome} ({self.funcao}) - {self.grupo.nome_grupo}"
        return f"{self.nome} - {self.grupo.nome_grupo}"
