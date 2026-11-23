# Prospect AI — Plataforma Autônoma de Prospecção Comercial B2B

O **Prospect AI** é uma solução completa de prospecção comercial automatizada para WhatsApp, desenvolvida com arquitetura profissional de ponta a ponta em **Python (FastAPI + Celery + Redis + PostgreSQL)** e **Next.js (React 19 + TypeScript + Tailwind CSS)**.

> **IMPORTANTE:** O sistema **não utiliza n8n, Make, Zapier ou intermediários externos**. Toda a lógica de filas, agendamento de follow-ups, controle de limites diários e execução contínua opera nativamente no backend via Celery Beat e Celery Worker.

---

## 🚀 Como Funciona a Automação 24/7 (EasyPanel / VPS)

O sistema opera como uma **automação inteligente contínua**:
1. **Fila Automática:** Todo lead extraído ou importado entra automaticamente na fila de prospecção.
2. **Execução Autônoma via Celery Beat:** A cada 60 segundos, o agendador Celery Beat verifica a fila.
3. **Respeito aos Horários e Dias:** Os disparos ocorrem **estritamente dentro da janela permitida** (ex: 07:00 às 18:30 no fuso de Brasília) e nos dias selecionados (Segunda a Sexta). Fora da janela, o motor entra em pausa obrigatória automaticamente.
4. **Sequência Conversacional de 3 Mensagens:** Quando um lead é contatado, o sistema dispara a Parte 1, faz uma pausa humana de digitação (8 a 14s), dispara a Parte 2 e a Parte 3.
5. **Cota de Compliance:** Respeita o teto diário de até 30 novos contatos/dia, evitando banimentos no WhatsApp.
6. **Controle com 1 Clique:** Na tela **Automação IA**, você pode pausar ou reativar os disparos instantaneamente.

---

## 🛠️ Como Subir no GitHub e Deploy no EasyPanel

### Passo 1: Subir para o seu GitHub
No terminal da raiz do projeto:
```bash
git init
git add .
git commit -m "feat: Prospect AI com Automação Contínua e Integração Evolution API"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```
*(O arquivo `.gitignore` já protege credenciais, bancos locais e pastas desnecessárias).*

### Passo 2: Criar Projeto no EasyPanel
1. No painel do seu **EasyPanel**, clique em **New Project** (ex: `prospect-ai`).
2. Adicione os serviços via **Docker Compose**:
   - Clique em **+ Service** -> **Docker Compose**
   - Conecte ao seu repositório GitHub (ou cole o conteúdo do `docker-compose.yml`).
3. Configure as variáveis de ambiente (`Environment Variables`):
   - `NEXT_PUBLIC_API_URL`: `https://SEU_DOMINIO_BACKEND/api/v1` (a URL pública do backend)
   - `DATABASE_URL`: gerenciado internamente pelo Docker Compose
   - `EVOLUTION_API_URL`: URL da sua Evolution API
   - `EVOLUTION_API_KEY`: API Key da sua Evolution
   - `EVOLUTION_INSTANCE_NAME`: Nome da instância (ex: `Carlos1`)
   - `GROQ_API_KEY`: Sua chave da Groq
4. Clique em **Deploy**. O EasyPanel iniciará:
   - `postgres`: Banco de dados relacional
   - `redis`: Gerenciador de filas em memória
   - `backend`: API FastAPI
   - `celery_worker`: Processador de mensagens e IA
   - `celery_beat`: Agendador 24/7 de horário e fila
   - `frontend`: Aplicação web Next.js

---

## 📱 Principais Módulos da Plataforma

1. **Dashboard Operacional**
   - Indicadores em tempo real: Total de leads, contatos enviados hoje, vagas restantes no limite diário (máx 30/dia), mensagens enviadas, respostas recebidas, oportunidades interessadas e campanhas ativas.
   - Gráfico de histórico dos últimos 7 dias (disparos vs respostas) e distribuição percentual por nicho de atuação.
   - Monitor de status da janela de envio útil (07:00 às 18:30 no fuso de São Paulo).

2. **Extrator de Leads (Lead Acquisition Service)**
   - Arquitetura de adaptadores extensíveis (Google Places API e OpenStreetMap/Nominatim).
   - Normalização automática de telefones brasileiros e internacionais em formato **E.164** (`+55...`).
   - Deduplicação inteligente e associação automática às campanhas selecionadas.

3. **Gerenciador de Leads**
   - Tabela de dados com filtros múltiplos (status, presença de telefone/website, nicho, cidade).
   - Ações em lote: vinculação à campanha e bloqueio com inclusão imediata na lista de supressão (opt-out).
   - Drawer de detalhes do lead com dados cadastrais, análise do website e visualização da sequência de 3 mensagens.

4. **Gerenciador de Campanhas & Motor de Envio (Campaign Execution Engine)**
   - Fluxo de criação em etapas.
   - **Limite diário obrigatório e atômico:** estritamente limitado a **30 contatos únicos por dia** em nível global.
   - **Horário de funcionamento obrigatório:** envios permitidos apenas das **07:00 às 18:30 (America/Sao_Paulo)**.
   - **Pausa e Retomada Automática:** às 18:30 os disparos são interrompidos; às 07:00 a fila retoma automaticamente.
   - Intervalos com jitter humano entre contatos (3 a 6 minutos) e intervalos configuráveis entre follow-ups (24h / 48h).

5. **Central de Inteligência Artificial & Fallback Automático**
   - Integração tripla nativa com **OpenAI**, **Groq** e **Google Gemini**.
   - Camada de abstração de provedores com fallback automático em caso de esgotamento de quota (429) ou erro de rede.
   - Saída estruturada estritamente validada via Pydantic (`messages: [part 1, part 2, part 3]`).

6. **Análise Segura de Websites com Proteção SSRF**
   - Scraper institucional que extrai propostas de valor públicas e diferenciais do estabelecimento sem inventar fatos.
   - Proteção avançada contra SSRF: bloqueio de redes privadas (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`), metadados de nuvem (`169.254.169.254`) e links de redes sociais.

7. **WhatsApp CRM (Evolution API)**
   - Integração nativa com instâncias da **Evolution API**.
   - Interface em 3 colunas inspirada em CRM (Lista de contatos, timeline de mensagens e ficha do lead).
   - Permite responder manualmente em tempo real.
   - Webhook idempotente para recebimento de mensagens e confirmações de entrega.
   - **Cancelamento automático:** se o lead responde ou solicita parada ("pare", "sair", etc.), todas as mensagens futuras da sequência são canceladas e o lead é classificado.

8. **Relatórios e Métricas**
   - Indicadores consolidados de taxa de resposta e taxa de interesse.
   - Tabelas de performance por campanha, segmento e eficácia por provedor de IA.
   - Exportação completa dos leads em formato CSV (UTF-8 com BOM).

---

## 🛠️ Stack Tecnológica

- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide React.
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic.
- **Banco de Dados:** PostgreSQL 16.
- **Fila e Agendamento:** Redis 7 e Celery (Worker + Beat).
- **Containerização:** Docker & Docker Compose.

---

## 📦 Como Executar com Docker Compose

Suba todo o ecossistema (PostgreSQL, Redis, Backend, Celery Worker, Celery Beat e Frontend) com um único comando:

```bash
docker compose up --build -d
```

Após a inicialização dos contêineres:
- **Frontend (Aplicação Web):** [http://localhost:3000](http://localhost:3000)
- **Backend (FastAPI & Swagger Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Healthcheck:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 💻 Como Executar em Ambiente Local (Desenvolvimento)

### 1. Backend (FastAPI + Celery)

```bash
cd backend
python -m pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

Para iniciar o worker e beat do Celery:
```bash
# Terminal 2 - Worker
celery -A app.celery_app.celery worker --loglevel=info

# Terminal 3 - Beat (Scheduler)
celery -A app.celery_app.celery beat --loglevel=info
```

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Acesse [http://localhost:3000](http://localhost:3000).

---

## 🧪 Testes Automatizados

A suíte de testes cobre todas as regras críticas de compliance, agendamento, proteção contra SSRF e concorrência:

```bash
python -m pytest backend/tests -v
```

### Casos de teste validados (17/17 aprovados):
- `test_window_open_at_10am`: Validação da abertura no fuso de SP.
- `test_window_closed_at_19pm`: Validação da pausa obrigatória pós-18:30.
- `test_daily_limit_blocks_31st_contact`: Bloqueio transacional do 31º contato do dia.
- `test_same_contact_does_not_consume_second_slot`: Validação de não consumo de cota para follow-ups.
- `test_ssrf_blocks_localhost`, `test_ssrf_blocks_127_0_0_1`, `test_ssrf_blocks_private_subnet_192_168`, `test_ssrf_blocks_social_media_instagram`: Testes de segurança de rede.
- `test_ai_fallback_on_primary_failure`: Validação do fallback entre OpenAI/Groq/Gemini.
- `test_webhook_idempotency`: Deduplicação garantida por event_id.
- `test_webhook_incoming_cancels_future_sequence_messages`: Cancelamento em tempo real da sequência ao receber resposta.
- `test_webhook_opt_out_stop_keyword_adds_to_suppression_list`: Supressão automática ao detectar intenção de saída.
