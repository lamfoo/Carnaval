from django.contrib import admin
from django.utils.html import format_html
from .models import Grupo, Categoria, Participante


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = [
        'nome',
        'codigo', 
        'icone_preview',
        'cor_preview',
        'ativa',
        'ordem'
    ]
    list_filter = ['ativa']
    search_fields = ['nome', 'codigo', 'descricao']
    list_editable = ['ativa', 'ordem']
    prepopulated_fields = {'codigo': ('nome',)}
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'codigo', 'descricao')
        }),
        ('Aparência', {
            'fields': ('icone', 'cor_primaria', 'cor_secundaria')
        }),
        ('Configurações', {
            'fields': ('ativa', 'ordem')
        }),
    )
    
    def icone_preview(self, obj):
        """Preview of the Bootstrap icon"""
        return format_html(
            '<i class="{}" style="font-size: 1.2rem; color: {};"></i>',
            obj.icone,
            obj.cor_primaria
        )
    icone_preview.short_description = "Ícone"
    
    def cor_preview(self, obj):
        """Preview of the category colors"""
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<div style="width: 20px; height: 20px; background: {}; border-radius: 3px; border: 1px solid #ddd;"></div>'
            '<div style="width: 20px; height: 20px; background: {}; border-radius: 3px; border: 1px solid #ddd;"></div>'
            '</div>',
            obj.cor_primaria,
            obj.cor_secundaria
        )
    cor_preview.short_description = "Cores"


class ParticipanteInline(admin.TabularInline):
    model = Participante
    extra = 1
    fields = ['nome', 'funcao', 'telefone', 'email', 'ativo']
    readonly_fields = ['data_adicao']


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = [
        'nome_grupo', 
        'categoria_display', 
        'representante', 
        'contato_display',
        'participantes_count',
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
    inlines = [ParticipanteInline]
    
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
        if obj.categoria:
            return format_html(
                '<span style="background: linear-gradient(45deg, {}, {}); color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem;">'
                '<i class="{}"></i> {}'
                '</span>',
                obj.categoria.cor_primaria,
                obj.categoria.cor_secundaria,
                obj.categoria.icone,
                obj.categoria.nome
            )
        return "Sem categoria"
    categoria_display.short_description = "Categoria"
    
    def contato_display(self, obj):
        """Display contact with appropriate icon"""
        if '@' in obj.contato:
            return format_html(
                '<i class="bi bi-envelope"></i> {}',
                obj.contato
            )
        else:
            return format_html(
                '<i class="bi bi-telephone"></i> {}',
                obj.contato
            )
    contato_display.short_description = "Contato"
    
    def participantes_count(self, obj):
        """Display number of participants"""
        count = obj.participantes.filter(ativo=True).count()
        return format_html(
            '<span style="background: #17a2b8; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8rem;">'
            '{} participantes'
            '</span>',
            count
        )
    participantes_count.short_description = "Participantes"
    
    def ativo_display(self, obj):
        """Display active status with colored icon"""
        if obj.ativo:
            return format_html(
                '<span style="color: green;">✓ Ativo</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Inativo</span>'
            )
    ativo_display.short_description = "Status"
    
    def foto_preview(self, obj):
        """Display photo thumbnail"""
        if obj.foto:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px;" />',
                obj.foto.url
            )
        return format_html(
            '<div style="width: 50px; height: 50px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; display: flex; align-items: center; justify-content: center;">'
            '<i class="bi bi-image" style="color: #6c757d;"></i>'
            '</div>'
        )
    foto_preview.short_description = "Foto"
    
    def get_queryset(self, request):
        """Optimize database queries"""
        return super().get_queryset(request).select_related('categoria').prefetch_related('participantes')


@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = [
        'nome',
        'funcao',
        'grupo_display',
        'telefone',
        'email',
        'idade_display',
        'ativo',
        'data_adicao'
    ]
    list_filter = [
        'grupo__categoria',
        'grupo',
        'funcao',
        'ativo',
        'data_adicao'
    ]
    search_fields = [
        'nome',
        'funcao',
        'grupo__nome_grupo',
        'telefone',
        'email'
    ]
    list_editable = ['ativo']
    readonly_fields = ['data_adicao']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('grupo', 'nome', 'funcao')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Informações Pessoais', {
            'fields': ('data_nascimento',),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('ativo', 'data_adicao'),
            'classes': ('collapse',)
        }),
    )
    
    def grupo_display(self, obj):
        """Display group with category badge"""
        if obj.grupo and obj.grupo.categoria:
            return format_html(
                '<strong>{}</strong><br>'
                '<small style="background: {}; color: white; padding: 2px 6px; border-radius: 8px;">'
                '{}'
                '</small>',
                obj.grupo.nome_grupo,
                obj.grupo.categoria.cor_primaria,
                obj.grupo.categoria.nome
            )
        return obj.grupo.nome_grupo if obj.grupo else "Sem grupo"
    grupo_display.short_description = "Grupo"
    
    def idade_display(self, obj):
        """Display age if birth date is available"""
        if obj.data_nascimento:
            from datetime import date
            today = date.today()
            age = today.year - obj.data_nascimento.year
            if today.month < obj.data_nascimento.month or (today.month == obj.data_nascimento.month and today.day < obj.data_nascimento.day):
                age -= 1
            return f"{age} anos"
        return "N/A"
    idade_display.short_description = "Idade"
    
    def get_queryset(self, request):
        """Optimize database queries"""
        return super().get_queryset(request).select_related('grupo__categoria')


# Customize admin site header
admin.site.site_header = "Administração - Carnaval da Beira"
admin.site.site_title = "Carnaval da Beira"
admin.site.index_title = "Painel Administrativo"
