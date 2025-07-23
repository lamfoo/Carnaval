from django.contrib import admin
from django.utils.html import format_html
from .models import Grupo


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = [
        'nome_grupo', 
        'categoria_display', 
        'representante', 
        'contato_display',
        'ativo',
        'ativo_display',
        'data_inscricao',
        'foto_preview'
    ]
    list_filter = [
        'categoria',
        'ativo',
        'data_inscricao',
    ]
    search_fields = [
        'nome_grupo',
        'representante',
        'contato',
        'descricao'
    ]
    list_editable = ['ativo']
    readonly_fields = ['data_inscricao']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_grupo', 'representante', 'contato', 'categoria')
        }),
        ('Descrição', {
            'fields': ('descricao',)
        }),
        ('Mídia', {
            'fields': ('foto',)
        }),
        ('Configurações', {
            'fields': ('ativo', 'data_inscricao'),
            'classes': ('collapse',)
        }),
    )
    
    def categoria_display(self, obj):
        """Display category with colored badge"""
        color = '#28a745' if obj.categoria == 'escola_samba' else '#007bff'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_categoria_display()
        )
    categoria_display.short_description = 'Categoria'
    
    def ativo_display(self, obj):
        """Display active status with icon"""
        if obj.ativo:
            return format_html(
                '<span style="color: green;">✓ Ativo</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Inativo</span>'
            )
    ativo_display.short_description = 'Status'
    
    def contato_display(self, obj):
        """Display contact with proper formatting"""
        if '@' in obj.contato:
            return format_html(
                '<a href="mailto:{}">{}</a>',
                obj.contato,
                obj.contato
            )
        else:
            return obj.contato
    contato_display.short_description = 'Contato'
    
    def foto_preview(self, obj):
        """Display photo preview"""
        if obj.foto:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 25px;"/>',
                obj.foto.url
            )
        return "Sem foto"
    foto_preview.short_description = 'Foto'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related()
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
