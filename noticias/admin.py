from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Noticia


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = [
        'titulo',
        'autor',
        'publicada',
        'destaque',
        'publicada_display',
        'destaque_display',
        'data_publicacao',
        'is_recent_display',
        'imagem_preview'
    ]
    list_filter = [
        'publicada',
        'destaque',
        'data_publicacao',
        'autor'
    ]
    search_fields = [
        'titulo',
        'conteudo',
        'autor'
    ]
    list_editable = ['publicada', 'destaque']
    readonly_fields = ['data_publicacao']
    date_hierarchy = 'data_publicacao'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'autor')
        }),
        ('Conteúdo', {
            'fields': ('conteudo',)
        }),
        ('Mídia', {
            'fields': ('imagem',)
        }),
        ('Publicação', {
            'fields': ('publicada', 'destaque', 'data_publicacao'),
            'classes': ('collapse',)
        }),
    )
    
    def publicada_display(self, obj):
        """Display publication status with icon"""
        if obj.publicada:
            return format_html(
                '<span style="color: green;">✓ Publicada</span>'
            )
        else:
            return format_html(
                '<span style="color: orange;">📝 Rascunho</span>'
            )
    publicada_display.short_description = 'Status'
    
    def destaque_display(self, obj):
        """Display highlight status"""
        if obj.destaque:
            return format_html(
                '<span style="color: gold;">⭐ Destaque</span>'
            )
        else:
            return '-'
    destaque_display.short_description = 'Destaque'
    
    def is_recent_display(self, obj):
        """Display if news is recent"""
        if obj.is_recent:
            return format_html(
                '<span style="color: blue;">🆕 Recente</span>'
            )
        else:
            return '-'
    is_recent_display.short_description = 'Recente'
    
    def imagem_preview(self, obj):
        """Display image preview"""
        if obj.imagem:
            return format_html(
                '<img src="{}" width="60" height="45" style="border-radius: 3px;"/>',
                obj.imagem.url
            )
        return "Sem imagem"
    imagem_preview.short_description = 'Imagem'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request)
    
    def save_model(self, request, obj, form, change):
        """Auto-set author if not provided"""
        if not obj.autor and request.user.is_authenticated:
            obj.autor = request.user.get_full_name() or request.user.username
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
