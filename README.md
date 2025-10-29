# Dashboard de Dados em Tempo Real

Dashboard interativo para monitoramento de sensores, finanças, tráfego e clima em tempo real usando Django Channels, Celery, Plotly Dash e integração com MQTT/Kafka.

## 🚀 Funcionalidades

- **Monitoramento em Tempo Real**: WebSockets via Django Channels
- **Visualizações Interativas**: Plotly Dash com gráficos dinâmicos
- **Processamento Assíncrono**: Celery para tarefas em background
- **Múltiplas Fontes de Dados**:
  - Sensores via MQTT
  - Finanças via Alpha Vantage API
  - Clima via OpenWeather API
  - Tráfego (simulado/API)
  - Eventos via Kafka

## 📋 Pré-requisitos

- Python 3.9+
- Redis Server
- (Opcional) MQTT Broker (ex: Mosquitto)
- (Opcional) Apache Kafka

## 🔧 Instalação

### 1. Clone e configure o ambiente

```bash
cd /Users/medrobotsmac/Documents/DjangoProject

# Ative o ambiente virtual
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configure as variáveis de ambiente

```bash
# Copie o template
cp .env.example .env

# Edite .env e adicione suas API keys
nano .env
```

**Obtenha suas API keys:**
- OpenWeather: https://openweathermap.org/api
- Alpha Vantage: https://www.alphavantage.co/support/#api-key

### 3. Configure o banco de dados

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Crie um superusuário

```bash
python manage.py createsuperuser
```

## ▶️ Executando o Projeto

### Opção 1: Script Automatizado (Recomendado)

```bash
# Torne o script executável (apenas primeira vez)
chmod +x run_dashboard.sh

# Execute tudo de uma vez (Redis, Celery, Django)
./run_dashboard.sh
```

O script inicia automaticamente:
- Redis Server
- Celery Worker
- Celery Beat (tarefas periódicas)
- Django Development Server

Acesse: **http://localhost:8000**

### Opção 2: Modo Desenvolvimento (sem Redis)

```bash
CHANNEL_LAYER_BACKEND=memory SKIP_REDIS_LAUNCH=1 ./run_dashboard.sh
```

### Opção 3: Manual (para desenvolvimento)

Em terminais separados:

```bash
# Terminal 1 - Redis
redis-server

# Terminal 2 - Celery Worker
celery -A DjangoProject worker --loglevel=info

# Terminal 3 - Celery Beat
celery -A DjangoProject beat --loglevel=info

# Terminal 4 - Django Server
python manage.py runserver

# Terminal 5 (Opcional) - MQTT/Kafka Bridges
python manage.py start_stream_bridges
```

## 📊 Estrutura do Dashboard

### Gráficos Disponíveis

1. **Sensor Streams**: Leituras de sensores em tempo real
2. **Financial Quotes**: Cotações de ações
3. **Traffic Congestion**: Índice de congestionamento
4. **Weather**: Temperatura e umidade

### Admin Django

Acesse o painel administrativo em: **http://localhost:8000/admin**

Gerencie:
- Leituras de sensores
- Métricas financeiras
- Atualizações de tráfego
- Dados meteorológicos

## 🔌 Integrações

### MQTT

Configure no `.env`:
```env
MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_TOPICS=sensors/temperature,sensors/humidity
```

Inicie o bridge:
```bash
python manage.py start_stream_bridges
```

### Kafka

Configure no `.env`:
```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPICS=dashboard-events
```

### APIs Externas

**OpenWeather**: Atualiza a cada 30 segundos
**Alpha Vantage**: Atualiza a cada 20 segundos
**Traffic**: Atualiza a cada 15 segundos

## 🛠️ Comandos Úteis

```bash
# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic

# Testar task do Celery manualmente
python manage.py shell
>>> from dashboard.tasks import fetch_weather
>>> fetch_weather.delay()

# Ver status das tasks no Celery
celery -A DjangoProject inspect active

# Limpar banco de dados (cuidado!)
python manage.py flush
```

## 📁 Estrutura do Projeto

```
DjangoProject/
├── dashboard/
│   ├── dash_apps/          # Aplicações Plotly Dash
│   ├── integrations/       # MQTT, Kafka bridges
│   ├── management/         # Comandos Django personalizados
│   ├── migrations/         # Migrações do banco
│   ├── admin.py           # Configuração admin
│   ├── consumers.py       # WebSocket consumers
│   ├── models.py          # Modelos de dados
│   ├── signals.py         # Sinais para broadcast
│   ├── tasks.py           # Tasks Celery
│   └── views.py           # Views Django
├── DjangoProject/
│   ├── asgi.py            # Configuração ASGI
│   ├── celery.py          # Configuração Celery
│   ├── routing.py         # Rotas WebSocket
│   ├── settings.py        # Configurações Django
│   └── urls.py            # URLs principais
├── static/                # Arquivos estáticos
├── templates/             # Templates HTML
├── .env.example           # Template de variáveis
├── requirements.txt       # Dependências Python
└── run_dashboard.sh       # Script de execução
```

## 🐛 Troubleshooting

### Erro: "Connection refused" (Redis)

```bash
# Instale o Redis
brew install redis

# Ou use modo em memória
CHANNEL_LAYER_BACKEND=memory SKIP_REDIS_LAUNCH=1 ./run_dashboard.sh
```

### Erro: "slots" no dataclass

Certifique-se de que está usando Python 3.9 e que `dashboard/realtime.py` não tem `@dataclass(slots=True)`.

### WebSocket não conecta

Verifique se o Redis está rodando:
```bash
redis-cli ping
# Deve retornar: PONG
```

### Gráficos não atualizam

1. Verifique se as API keys estão configuradas no `.env`
2. Confirme que o Celery Beat está rodando
3. Veja os logs do Celery para erros

## 📦 Dependências Principais

- **Django 4.2.25**: Framework web
- **Channels 4.1.0**: WebSockets
- **Celery 5.4.0**: Processamento assíncrono
- **Plotly Dash 2.17.1**: Visualizações interativas
- **Redis 5.0.4**: Cache e message broker
- **paho-mqtt 2.1.0**: Cliente MQTT
- **kafka-python 2.0.2**: Cliente Kafka

## 🔒 Segurança

Para produção:
1. Altere `SECRET_KEY` no `.env`
2. Configure `DEBUG=0`
3. Use HTTPS (configure `SECURE_SSL_REDIRECT=True`)
4. Configure firewalls adequados
5. Use variáveis de ambiente para credenciais

## 📄 Licença

Este projeto é um exemplo educacional.

## 👥 Contribuindo

Este é um projeto de demonstração. Sinta-se livre para adaptá-lo às suas necessidades.

## 📧 Suporte

Para problemas ou dúvidas, verifique:
- Logs do Celery: saída do terminal
- Logs do Django: saída do servidor
- Redis: `redis-cli monitor`
