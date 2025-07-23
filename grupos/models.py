from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import os


def grupo_photo_upload_path(instance, filename):
    """Upload path for group photos"""
    return f'grupos/{instance.nome_grupo}/{filename}'


class Grupo(models.Model):
    CATEGORIA_CHOICES = [
        ('escola_samba', 'Escola de Samba'),
        ('bloco_rua', 'Bloco de Rua'),
    ]
    
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
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name="Categoria"
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
        
    def get_categoria_display_custom(self):
        """Custom display for category"""
        return dict(self.CATEGORIA_CHOICES)[self.categoria]
        
    def save(self, *args, **kwargs):
        # Ensure nome_grupo is properly formatted
        self.nome_grupo = self.nome_grupo.strip().title()
        super().save(*args, **kwargs)
