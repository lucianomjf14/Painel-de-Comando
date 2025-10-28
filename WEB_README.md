# 🌐 Google Automation Dashboard - Interface Web

Uma interface web moderna e intuitiva para gerenciar Google Sheets, Gmail e Google Drive através de uma aplicação Flask.

## 🚀 Início Rápido

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar a Aplicação Web
```bash
python start_web.py
```

A aplicação será iniciada em `http://localhost:5000` e o navegador será aberto automaticamente.

## 📱 Funcionalidades da Interface Web

### 🏠 Página Inicial
- **Dashboard principal** com visão geral das APIs
- **Cards informativos** para Gmail, Sheets e Drive
- **Status em tempo real** da conexão com as APIs
- **Navegação intuitiva** entre as seções

### 📧 Gmail Manager
- **Contagem de mensagens não lidas** em tempo real
- **Listagem de mensagens** com filtros avançados
- **Busca de mensagens** com queries do Gmail
- **Envio de emails** através de formulário
- **Visualização de labels** e organização
- **Interface responsiva** para mobile e desktop

### 📊 Google Sheets Manager
- **Criação de novas planilhas** com um clique
- **Listagem de planilhas** existentes
- **Visualização de dados** em tabelas
- **Abertura direta** no Google Sheets
- **Estatísticas** de planilhas (total, recentes, compartilhadas)

### 💾 Google Drive Manager
- **Upload de arquivos** com drag & drop
- **Visualização em grid e lista**
- **Filtros por tipo de arquivo**
- **Busca de arquivos** avançada
- **Estatísticas** de uso do Drive
- **Abertura direta** de arquivos

## 🎨 Design e UX

### Características Visuais
- **Design moderno** com Bootstrap 5
- **Cores do Google** (azul, verde, vermelho, amarelo)
- **Ícones Font Awesome** para melhor identificação
- **Animações suaves** e transições
- **Responsivo** para todos os dispositivos

### Experiência do Usuário
- **Interface intuitiva** e fácil de usar
- **Feedback visual** para todas as ações
- **Alertas informativos** para sucessos e erros
- **Loading states** durante operações
- **Auto-refresh** para dados em tempo real

## 🔧 Configuração Técnica

### Estrutura da Aplicação
```
├── app.py                 # Aplicação Flask principal
├── start_web.py          # Script de inicialização
├── templates/            # Templates HTML
│   ├── base.html        # Template base
│   ├── index.html       # Página inicial
│   ├── gmail.html       # Interface Gmail
│   ├── sheets.html      # Interface Sheets
│   └── drive.html       # Interface Drive
├── static/              # Arquivos estáticos
│   ├── css/
│   │   └── style.css    # Estilos customizados
│   └── js/
│       └── main.js      # JavaScript principal
└── WEB_README.md        # Esta documentação
```

### APIs Disponíveis

#### Gmail API
- `GET /api/gmail/unread-count` - Conta mensagens não lidas
- `GET /api/gmail/messages` - Lista mensagens
- `GET /api/gmail/labels` - Lista labels
- `POST /api/gmail/send` - Envia email

#### Google Sheets API
- `GET /api/sheets/list` - Lista planilhas
- `POST /api/sheets/create` - Cria planilha
- `GET /api/sheets/read` - Lê dados da planilha

#### Google Drive API
- `GET /api/drive/list` - Lista arquivos
- `POST /api/drive/upload` - Upload de arquivo

## 🚀 Como Usar

### 1. Acessar a Interface
1. Execute `python start_web.py`
2. Aguarde o navegador abrir automaticamente
3. Acesse `http://localhost:5000`

### 2. Navegar pelas Seções
- **Home**: Dashboard principal com visão geral
- **Gmail**: Gerenciar emails e mensagens
- **Sheets**: Criar e gerenciar planilhas
- **Drive**: Upload e gerenciar arquivos

### 3. Funcionalidades Principais

#### Gmail
- Visualize mensagens não lidas
- Busque mensagens com filtros
- Envie emails diretamente
- Organize com labels

#### Sheets
- Crie novas planilhas
- Visualize dados existentes
- Abra planilhas no Google Sheets

#### Drive
- Faça upload de arquivos
- Navegue pelos arquivos
- Filtre por tipo de arquivo
- Abra arquivos diretamente

## 🔒 Segurança

- **Autenticação OAuth 2.0** com Google
- **Tokens seguros** armazenados localmente
- **CORS configurado** para segurança
- **Validação de dados** em todas as APIs

## 🛠️ Desenvolvimento

### Modo Debug
A aplicação roda em modo debug por padrão, permitindo:
- **Hot reload** de mudanças
- **Logs detalhados** de erros
- **Debugging** facilitado

### Personalização
- **CSS customizado** em `static/css/style.css`
- **JavaScript** em `static/js/main.js`
- **Templates** em `templates/`

## 📱 Responsividade

A interface é totalmente responsiva e funciona em:
- **Desktop** (1200px+)
- **Tablet** (768px - 1199px)
- **Mobile** (até 767px)

## 🎯 Próximas Funcionalidades

- [ ] **Chat em tempo real** para colaboração
- [ ] **Notificações push** para novos emails
- [ ] **Temas personalizáveis** (claro/escuro)
- [ ] **Exportação de dados** em múltiplos formatos
- [ ] **Integração com calendário** Google
- [ ] **Relatórios avançados** e analytics

## 🐛 Solução de Problemas

### Erro de Conexão
- Verifique se as credenciais estão configuradas
- Execute `python cli.py auth login` para reautenticar

### Erro de Upload
- Verifique o tamanho do arquivo (máximo 5GB)
- Confirme as permissões do Google Drive

### Erro de API
- Verifique se as APIs estão ativadas no Google Cloud Console
- Confirme os escopos de permissão

## 📞 Suporte

Para suporte técnico ou dúvidas:
1. Verifique a documentação completa
2. Execute os testes de conectividade
3. Consulte os logs da aplicação

---

**Desenvolvido com ❤️ usando Python Flask e Google APIs**
