from django.db import models
from django.utils import timezone
from ckeditor.fields import RichTextField
import os


def noticia_image_upload_path(instance, filename):
    """Upload path for news images"""
    date_str = instance.data_publicacao.strftime('%Y/%m')
    return f'noticias/{date_str}/{filename}'


class Noticia(models.Model):
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título",
        help_text="Título da notícia"
    )
    conteudo = RichTextField(
        verbose_name="Conteúdo",
        help_text="Conteúdo completo da notícia com formatação rica"
    )
    imagem = models.ImageField(
        upload_to=noticia_image_upload_path,
        blank=True,
        null=True,
        verbose_name="Imagem",
        help_text="Imagem destacada da notícia"
    )
    data_publicacao = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data de Publicação"
    )
    publicada = models.BooleanField(
        default=True,
        verbose_name="Publicada",
        help_text="Notícia visível ao público"
    )
    destaque = models.BooleanField(
        default=False,
        verbose_name="Destaque",
        help_text="Exibir como notícia em destaque"
    )
    autor = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Autor",
        help_text="Autor da notícia (opcional)"
    )
    
    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ['-data_publicacao']
        
    def __str__(self):
        return self.titulo
        
    def resumo(self, max_length=150):
        """Returns a summary of the content without HTML tags"""
        import re
        # Remove HTML tags for summary
        clean_content = re.sub('<.*?>', '', self.conteudo)
        if len(clean_content) <= max_length:
            return clean_content
        return clean_content[:max_length] + '...'
        
    @property
    def is_recent(self):
        """Check if news was published in the last 7 days"""
        from datetime import timedelta
        return timezone.now() - self.data_publicacao <= timedelta(days=7)
