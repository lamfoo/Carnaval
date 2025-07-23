# 🎭 Sistema Carnaval da Beira

Sistema completo de gerenciamento para o Carnaval da Beira, desenvolvido em Django 5.0 com funcionalidades de cadastro de grupos, notícias e sistema de votação popular.

## 🚀 Funcionalidades

### 1. **Cadastro de Grupos Participantes**
- ✅ Cadastro completo com nome único, representante, contato e categoria
- ✅ Upload de fotos dos grupos
- ✅ Validação de formato de contato (telefone ou email)
- ✅ Interface administrativa completa
- ✅ Categorias: Escola de Samba e Bloco de Rua

### 2. **Sistema de Notícias**
- ✅ Editor de texto rico (CKEditor)
- ✅ Upload de imagens para notícias
- ✅ Sistema de destaque para notícias importantes
- ✅ Ordenação por data de publicação
- ✅ Interface pública responsiva

### 3. **Sistema de Votação Popular**
- ✅ Votação segura por dispositivo (hash SHA-256)
- ✅ Limite de 1 voto por categoria por dispositivo
- ✅ Rate limiting para prevenir abuso
- ✅ Interface intuitiva de votação
- ✅ Resultados em tempo real com percentuais
- ✅ Auditoria completa de votos

### 4. **Interface Responsiva**
- ✅ Bootstrap 5 com design moderno
- ✅ Acessibilidade WCAG 2.1 nível AA
- ✅ Navegação por teclado
- ✅ Otimizado para dispositivos móveis

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.12 + Django 5.0
- **Frontend:** Bootstrap 5 + JavaScript ES6
- **Banco de Dados:** SQLite 3
- **Editor de Texto:** django-ckeditor
- **Segurança:** django-ratelimit + CSRF protection
- **Mídia:** Pillow para processamento de imagens

## 📋 Pré-requisitos

- Python 3.12 ou superior
- pip (gerenciador de pacotes Python)
- Git

## 🔧 Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd carnaval-da-beira
```

### 2. Crie e ative o ambiente virtual
```bash
python3 -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure o banco de dados
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crie um superusuário
```bash
python manage.py createsuperuser
```

### 6. Execute o servidor
```bash
python manage.py runserver
```

O sistema estará disponível em: `http://localhost:8000`

## 🔐 Acesso Administrativo

Acesse `http://localhost:8000/admin` com as credenciais do superusuário criado para:

- Cadastrar grupos participantes
- Gerenciar notícias
- Visualizar votos e estatísticas
- Administrar o sistema

## 📊 Estrutura do Banco de Dados

### Modelo Grupo
```
┌─────────────────┐
│     GRUPO       │
├─────────────────┤
│ id (PK)         │
│ nome_grupo      │ (UNIQUE)
│ representante   │
│ contato         │ (Validado)
│ descricao       │
│ categoria       │ (escola_samba/bloco_rua)
│ data_inscricao  │
│ foto            │ (ImageField)
│ ativo           │
└─────────────────┘
```

### Modelo Noticia
```
┌─────────────────┐
│    NOTICIA      │
├─────────────────┤
│ id (PK)         │
│ titulo          │
│ conteudo        │ (RichTextField)
│ imagem          │ (ImageField)
│ data_publicacao │
│ publicada       │
│ destaque        │
│ autor           │
└─────────────────┘
```

### Modelo Voto
```
┌─────────────────┐
│      VOTO       │
├─────────────────┤
│ id (PK)         │
│ grupo (FK)      │ → Grupo
│ categoria       │
│ device_id       │ (SHA-256)
│ ip_address      │
│ timestamp       │
└─────────────────┘
UNIQUE(device_id, categoria)
```

## 🔒 Segurança Implementada

### Votação Segura
- **Device ID:** Hash SHA-256 do IP + User-Agent
- **Rate Limiting:** 5 votos por minuto por IP
- **Validação CSRF:** Proteção contra ataques CSRF
- **Auditoria:** Log completo de todos os votos
- **Integridade:** Constraint único por dispositivo/categoria

### Proteções Gerais
- **XSS Prevention:** Sanitização de inputs
- **SQL Injection:** Django ORM
- **Clickjacking:** X-Frame-Options
- **Content Sniffing:** X-Content-Type-Options

## 🌐 URLs do Sistema

| URL | Descrição |
|-----|-----------|
| `/` | Página inicial |
| `/grupos/` | Lista de grupos |
| `/grupos/<id>/` | Detalhes do grupo |
| `/noticias/` | Lista de notícias |
| `/noticias/<id>/` | Detalhes da notícia |
| `/votacao/` | Sistema de votação |
| `/votacao/resultados/` | Resultados da votação |
| `/admin/` | Painel administrativo |

## 📱 Recursos de Acessibilidade

- **Navegação por teclado** completa
- **Screen readers** compatíveis
- **Contraste adequado** (WCAG AA)
- **Textos alternativos** em imagens
- **Landmarks ARIA** para navegação
- **Skip links** para conteúdo principal

## 🔄 Backup e Manutenção

### Backup do Banco de Dados
```bash
python manage.py dumpdata > backup.json
```

### Restaurar Backup
```bash
python manage.py loaddata backup.json
```

### Limpar Cache
```bash
python manage.py clearcache
```

## 📈 Monitoramento

### Logs de Votação
Todos os votos são registrados com:
- Timestamp completo
- IP do votante
- Device ID
- Grupo votado
- Categoria

### Estatísticas Disponíveis
- Total de votos por categoria
- Grupos mais votados
- Histórico de votação
- Sessões de usuários

## 🐛 Troubleshooting

### Problema: Erro de cache no django-ratelimit
**Solução:** É um warning normal em desenvolvimento. Em produção, configure um cache compartilhado (Redis/Memcached).

### Problema: Imagens não aparecem
**Solução:** Verifique se o `MEDIA_URL` e `MEDIA_ROOT` estão configurados corretamente.

### Problema: Erro ao fazer upload de imagens
**Solução:** Instale o Pillow: `pip install Pillow`

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Equipe de Desenvolvimento

- **Backend:** Django 5.0 + Python 3.12
- **Frontend:** Bootstrap 5 + JavaScript
- **Database:** SQLite com migrations
- **Security:** Rate limiting + CSRF + XSS protection

## 📞 Suporte

Para suporte técnico ou dúvidas sobre o sistema:

- 📧 Email: admin@carnavaldabeira.com
- 🐛 Issues: [GitHub Issues](../../issues)
- 📖 Documentação: Este README

---

**🎭 Carnaval da Beira - Celebrando nossa tradição!** 🎭