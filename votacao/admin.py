from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Voto, ResultadoVotacao, VotingSession, Payment


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = [
        'grupo',
        'categoria_display',
        'device_id_short',
        'ip_address',
        'timestamp'
    ]
    list_filter = [
        'categoria',
        'grupo',
        'timestamp'
    ]
    search_fields = [
        'grupo__nome_grupo',
        'device_id',
        'ip_address'
    ]
    readonly_fields = [
        'grupo',
        'categoria',
        'device_id',
        'ip_address',
        'timestamp'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Disable adding votes through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing votes through admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete votes"""
        return request.user.is_superuser
    
    def categoria_display(self, obj):
        """Display category with colored badge"""
        if obj.categoria:
            return format_html(
                '<span style="background: {}; color: white; padding: 2px 6px; '
                'border-radius: 3px; font-size: 10px;">{}</span>',
                obj.categoria.cor_primaria,
                obj.categoria.nome
            )
        return "Sem categoria"
    categoria_display.short_description = 'Categoria'
    
    def device_id_short(self, obj):
        """Display shortened device ID"""
        return f"{obj.device_id[:8]}...{obj.device_id[-4:]}"
    device_id_short.short_description = 'Device ID'


@admin.register(ResultadoVotacao)
class ResultadoVotacaoAdmin(admin.ModelAdmin):
    list_display = [
        'categoria_display',
        'total_votos',
        'ultimo_update',
        'porcentagem_display'
    ]
    readonly_fields = [
        'categoria',
        'total_votos',
        'ultimo_update'
    ]
    
    def has_add_permission(self, request):
        """Disable adding results through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing results through admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete results"""
        return request.user.is_superuser
    
    def categoria_display(self, obj):
        """Display category with colored badge"""
        if obj.categoria:
            return format_html(
                '<span style="background: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">{}</span>',
                obj.categoria.cor_primaria,
                obj.categoria.nome
            )
        return "Sem categoria"
    categoria_display.short_description = 'Categoria'
    
    def porcentagem_display(self, obj):
        """Display percentage of total votes"""
        total_geral = sum(ResultadoVotacao.objects.values_list('total_votos', flat=True))
        if total_geral > 0:
            percentage = (obj.total_votos / total_geral) * 100
            return f"{percentage:.1f}%"
        return "0%"
    porcentagem_display.short_description = 'Porcentagem'


@admin.register(VotingSession)
class VotingSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_key_short',
        'device_id_short',
        'votes_count',
        'created_at'
    ]
    list_filter = [
        'created_at',
        'votes_count'
    ]
    search_fields = [
        'session_key',
        'device_id'
    ]
    readonly_fields = [
        'session_key',
        'device_id',
        'created_at',
        'votes_count'
    ]
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        """Disable adding sessions through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing sessions through admin"""
        return False
    
    def session_key_short(self, obj):
        """Display shortened session key"""
        return f"{obj.session_key[:8]}..."
    session_key_short.short_description = 'Session Key'
    
    def device_id_short(self, obj):
        """Display shortened device ID"""
        return f"{obj.device_id[:8]}...{obj.device_id[-4:]}"
    device_id_short.short_description = 'Device ID'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_reference', 'customer_msisdn', 'amount', 
        'grupo', 'categoria_display', 'status', 'created_at'
    ]
    list_filter = ['status', 'categoria', 'created_at']
    search_fields = [
        'transaction_reference', 'customer_msisdn', 'grupo__nome_grupo',
        'conversation_id', 'transaction_id'
    ]
    readonly_fields = [
        'transaction_reference', 'third_party_reference', 'conversation_id',
        'transaction_id', 'response_code', 'response_desc', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('Informações do Pagamento', {
            'fields': [
                'transaction_reference', 'third_party_reference', 'customer_msisdn',
                'amount', 'status'
            ]
        }),
        ('Dados do Voto', {
            'fields': ['grupo', 'categoria', 'device_id', 'ip_address']
        }),
        ('Resposta M-Pesa', {
            'fields': [
                'conversation_id', 'transaction_id', 'response_code', 'response_desc'
            ]
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at', 'expires_at']
        }),
    ]
    
    def has_add_permission(self, request):
        """Disable add permission - payments are created automatically"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Only allow superusers to change payments"""
        return request.user.is_superuser
    
    def categoria_display(self, obj):
        """Display category with colored badge"""
        if obj.categoria:
            return format_html(
                '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8rem;">'
                '<i class="{}"></i> {}'
                '</span>',
                obj.categoria.cor_primaria,
                obj.categoria.icone,
                obj.categoria.nome
            )
        return "Sem categoria"
    categoria_display.short_description = 'Categoria'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


# Customize admin site header
admin.site.site_header = "Carnaval da Beira - Administração"
admin.site.site_title = "Carnaval da Beira Admin"
admin.site.index_title = "Painel de Administração do Carnaval"
