#!/usr/bin/env python
"""
Script to populate sample data for the Carnaval da Beira system
Run this script after migrations to create sample groups and news
"""

import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carnaval_beira.settings')
django.setup()

from grupos.models import Grupo
from noticias.models import Noticia
from django.utils import timezone

def create_sample_grupos():
    """Create sample groups for testing"""
    
    grupos_data = [
        # Escolas de Samba
        {
            'nome_grupo': 'Unidos da Beira',
            'representante': 'Maria Silva',
            'contato': '(11) 99999-1234',
            'descricao': 'Tradicional escola de samba da Beira, fundada em 1980. Conhecida por seus enredos históricos e alegoria exuberante.',
            'categoria': 'escola_samba',
        },
        {
            'nome_grupo': 'Estrela do Carnaval',
            'representante': 'João Santos',
            'contato': 'joao.santos@email.com',
            'descricao': 'Escola de samba jovem e vibrante, com foco em temas contemporâneos e inovação nas apresentações.',
            'categoria': 'escola_samba',
        },
        {
            'nome_grupo': 'Dragões da Beira',
            'representante': 'Ana Costa',
            'contato': '(11) 98765-4321',
            'descricao': 'Uma das mais antigas escolas de samba da região, famosa por seus desfiles temáticos sobre a cultura local.',
            'categoria': 'escola_samba',
        },
        
        # Blocos de Rua
        {
            'nome_grupo': 'Bloco da Alegria',
            'representante': 'Carlos Oliveira',
            'contato': 'carlos.alegria@gmail.com',
            'descricao': 'Bloco tradicional que anima as ruas da Beira há mais de 30 anos com música e muita animação.',
            'categoria': 'bloco_rua',
        },
        {
            'nome_grupo': 'Foliões da Madrugada',
            'representante': 'Lucia Ferreira',
            'contato': '(11) 97777-8888',
            'descricao': 'Bloco que sai nas primeiras horas da manhã, levando alegria e música para quem acorda cedo no carnaval.',
            'categoria': 'bloco_rua',
        },
        {
            'nome_grupo': 'Bambas do Samba',
            'representante': 'Roberto Lima',
            'contato': 'bambas.samba@outlook.com',
            'descricao': 'Bloco focado no samba de raiz e na preservação das tradições carnavalescas da região.',
            'categoria': 'bloco_rua',
        },
        {
            'nome_grupo': 'Cordão da Beira',
            'representante': 'Fernanda Souza',
            'contato': '(11) 96666-5555',
            'descricao': 'Cordão carnavalesco que preserva as tradições antigas do carnaval de rua com fantasias artesanais.',
            'categoria': 'bloco_rua',
        },
    ]
    
    created_grupos = []
    for grupo_data in grupos_data:
        grupo, created = Grupo.objects.get_or_create(
            nome_grupo=grupo_data['nome_grupo'],
            defaults=grupo_data
        )
        if created:
            created_grupos.append(grupo)
            print(f"✓ Criado grupo: {grupo.nome_grupo}")
        else:
            print(f"- Grupo já existe: {grupo.nome_grupo}")
    
    return created_grupos

def create_sample_noticias():
    """Create sample news for testing"""
    
    noticias_data = [
        {
            'titulo': 'Inscrições Abertas para o Carnaval da Beira 2025',
            'conteudo': '''
            <p>As inscrições para o <strong>Carnaval da Beira 2025</strong> estão oficialmente abertas!</p>
            
            <p>Este ano, esperamos receber ainda mais grupos participantes em nossas duas categorias:</p>
            <ul>
                <li>Escolas de Samba</li>
                <li>Blocos de Rua</li>
            </ul>
            
            <p>O prazo para inscrições vai até o dia 31 de janeiro. Não percam essa oportunidade de fazer parte da maior festa popular da nossa região!</p>
            
            <p>Para mais informações, procurem a secretaria de cultura ou acessem nosso sistema online.</p>
            ''',
            'autor': 'Prefeitura da Beira',
            'destaque': True,
        },
        {
            'titulo': 'Sistema de Votação Popular Já Está no Ar',
            'conteudo': '''
            <p>Novidade para este ano! Agora o público pode votar nos seus grupos favoritos através do nosso novo <strong>sistema de votação online</strong>.</p>
            
            <p>Como funciona:</p>
            <ul>
                <li>Cada pessoa pode votar uma vez por categoria</li>
                <li>A votação é segura e anônima</li>
                <li>Os resultados são atualizados em tempo real</li>
            </ul>
            
            <p>Participe e ajude a escolher os grupos mais queridos do Carnaval da Beira!</p>
            ''',
            'autor': 'Comissão Organizadora',
            'destaque': True,
        },
        {
            'titulo': 'Programação dos Ensaios Abertos',
            'conteudo': '''
            <p>Confira a programação dos ensaios abertos que acontecerão nos próximos fins de semana:</p>
            
            <p><strong>Sábado (25/01):</strong></p>
            <ul>
                <li>14h - Unidos da Beira</li>
                <li>16h - Bloco da Alegria</li>
                <li>18h - Estrela do Carnaval</li>
            </ul>
            
            <p><strong>Domingo (26/01):</strong></p>
            <ul>
                <li>15h - Dragões da Beira</li>
                <li>17h - Foliões da Madrugada</li>
                <li>19h - Bambas do Samba</li>
            </ul>
            
            <p>Todos os ensaios são gratuitos e abertos ao público!</p>
            ''',
            'autor': 'Coordenação dos Grupos',
            'destaque': False,
        },
        {
            'titulo': 'Regras e Critérios de Avaliação',
            'conteudo': '''
            <p>Para garantir um carnaval justo e organizado, divulgamos os <strong>critérios de avaliação</strong> dos grupos:</p>
            
            <h3>Escolas de Samba:</h3>
            <ul>
                <li>Harmonia e conjunto (30%)</li>
                <li>Enredo e desenvolvimento (25%)</li>
                <li>Fantasia e alegoria (25%)</li>
                <li>Evolução e coreografia (20%)</li>
            </ul>
            
            <h3>Blocos de Rua:</h3>
            <ul>
                <li>Animação e participação (40%)</li>
                <li>Criatividade (30%)</li>
                <li>Tradição e autenticidade (30%)</li>
            </ul>
            
            <p>A comissão julgadora será composta por especialistas em cultura popular e carnaval.</p>
            ''',
            'autor': 'Comissão Julgadora',
            'destaque': False,
        },
        {
            'titulo': 'Apoio Local: Empresas Patrocinadoras',
            'conteudo': '''
            <p>O Carnaval da Beira conta com o apoio fundamental de empresas locais que acreditam na nossa cultura!</p>
            
            <p>Agradecemos aos nossos patrocinadores:</p>
            <ul>
                <li>Supermercado Beira Mar</li>
                <li>Farmácia Central</li>
                <li>Restaurante Sabor Local</li>
                <li>Auto Peças Beira</li>
            </ul>
            
            <p>Sem o apoio da comunidade empresarial, não seria possível realizar este evento tão especial para nossa cidade.</p>
            
            <p>Ainda há oportunidades para novos patrocinadores! Entre em contato conosco.</p>
            ''',
            'autor': 'Departamento de Patrocínio',
            'destaque': False,
        },
    ]
    
    created_noticias = []
    for noticia_data in noticias_data:
        noticia, created = Noticia.objects.get_or_create(
            titulo=noticia_data['titulo'],
            defaults=noticia_data
        )
        if created:
            created_noticias.append(noticia)
            print(f"✓ Criada notícia: {noticia.titulo}")
        else:
            print(f"- Notícia já existe: {noticia.titulo}")
    
    return created_noticias

def main():
    """Main function to populate sample data"""
    print("🎭 Populando dados de exemplo para o Carnaval da Beira...")
    print()
    
    print("📝 Criando grupos de exemplo...")
    grupos = create_sample_grupos()
    print(f"✅ {len(grupos)} grupos criados")
    print()
    
    print("📰 Criando notícias de exemplo...")
    noticias = create_sample_noticias()
    print(f"✅ {len(noticias)} notícias criadas")
    print()
    
    print("🎉 Dados de exemplo criados com sucesso!")
    print()
    print("Agora você pode:")
    print("- Acessar /grupos/ para ver os grupos")
    print("- Acessar /noticias/ para ver as notícias")
    print("- Acessar /votacao/ para testar o sistema de votação")
    print("- Acessar /admin/ para gerenciar o conteúdo")

if __name__ == '__main__':
    main()