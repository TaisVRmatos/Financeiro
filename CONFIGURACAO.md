# 🚀 GUIA DE INSTALAÇÃO E DEPLOYMENT

## Instalação Local

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/integrador-financeiro.git
cd integrador-financeiro
```

### 2. Crie ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale dependências
```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação Streamlit
```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

---

## Deploy no Streamlit Cloud

### 1. Push para GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Acesse Streamlit Cloud
- Vá para https://share.streamlit.io
- Faça login com sua conta GitHub
- Clique "New app"
- Configure:
  - **Repository**: seu-usuario/integrador-financeiro
  - **Branch**: main
  - **Main file path**: app.py

### 3. Deploy
Clique "Deploy" e aguarde ~2 minutos

---

## Deploy na AWS (EC2)

### 1. Conecte à instância
```bash
ssh -i seu-arquivo.pem ec2-user@seu-ec2-public-ip
```

### 2. Instale Python e Git
```bash
sudo yum update
sudo yum install python3 python3-pip git
```

### 3. Clone e configure
```bash
git clone https://github.com/seu-usuario/integrador-financeiro.git
cd integrador-financeiro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Execute com Gunicorn (produção)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "streamlit.web.cli:main" -- run app.py --logger.level=error
```

### 5. Configure Nginx como reverse proxy
```bash
sudo yum install nginx
sudo systemctl start nginx
```

Adicione em `/etc/nginx/conf.d/streamlit.conf`:
```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo systemctl reload nginx
```

---

## Deploy no Heroku

### 1. Instale Heroku CLI
```bash
# https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Crie arquivo `Procfile`
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

### 3. Faça login e deploy
```bash
heroku login
heroku create seu-app-name
git push heroku main
```

---

## Docker

### 1. Crie `Dockerfile`
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Build e run
```bash
docker build -t integrador-financeiro .
docker run -p 8501:8501 integrador-financeiro
```

### 3. Push para Docker Hub
```bash
docker tag integrador-financeiro:latest seu-usuario/integrador-financeiro:latest
docker push seu-usuario/integrador-financeiro:latest
```

---

## Testando Localmente

### Teste rápido do processador
```bash
python3 << 'EOF'
from processor import process_integration, export_to_excel

result = process_integration(
    'Titulos_em_aberto_Matera.csv',
    'Título_em_Aberto.csv',
    'CR_MAXIFROTA_2026.xlsx'
)

export_to_excel(result, 'output.xlsx')
print(f"✅ {len(result)} registros processados")
EOF
```

### Teste do Streamlit
```bash
streamlit run app.py
# Abra http://localhost:8501
# Carregue os arquivos
# Clique em "Consolidar Dados"
# Baixe o resultado
```

---

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### Erro: "UnicodeDecodeError"
Os arquivos CSV usam encoding `iso-8859-1`. Se tiver problemas:
```bash
# Converter para UTF-8
iconv -f ISO-8859-1 -t UTF-8 input.csv -o output.csv
```

### Porta 8501 já em uso
```bash
streamlit run app.py --server.port=8502
```

### Aumentar timeout de upload
Edite `~/.streamlit/config.toml`:
```toml
[client]
maxUploadSize = 100

[server]
maxUploadSize = 100
```

---

## Variáveis de Ambiente (Produção)

Crie `.streamlit/secrets.toml`:
```toml
[database]
username = "seu_usuario"
password = "sua_senha"

[credentials]
api_key = "sua_chave_api"
```

Acesse em `app.py`:
```python
import streamlit as st
db_username = st.secrets["database"]["username"]
```

---

## GitHub Actions CI/CD

O repositório já inclui `.github/workflows/tests.yml` que executa:
- Linting com flake8
- Verificação de imports
- Testes com múltiplas versões Python

Os testes rodam automaticamente em cada `push` e `pull_request`.

---

## Performance e Otimizações

### Cachear operações
```python
@st.cache_data
def read_data(filepath):
    return pd.read_csv(filepath)
```

### Limpar memória
```bash
# Remover dados temporários
rm -f *.xlsx *.csv __pycache__/*
```

### Monitorar uso de memória
```bash
# Python
import psutil
print(f"Memória: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB")

# Sistema
free -h
top -n 1 | grep "Mem:"
```

---

## Segurança em Produção

### 1. HTTPS obrigatório
```bash
# Usar Let's Encrypt com Certbot
sudo certbot certonly --standalone -d seu-dominio.com
```

### 2. Rate limiting no Nginx
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location / {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://localhost:8000;
}
```

### 3. Validação de uploads
- Limite tamanho máximo de arquivo
- Validar extensão (.csv, .xlsx)
- Escanear malware (ClamAV)

### 4. Rotação de logs
```bash
# /etc/logrotate.d/streamlit
/var/log/streamlit/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
}
```

---

## Monitoramento

### Sentry (Error Tracking)
```bash
pip install sentry-sdk
```

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://sua-dsn@sentry.io/seu-project-id",
    traces_sample_rate=1.0
)
```

### Prometheus + Grafana (Métricas)
```python
from prometheus_client import Counter, Histogram

consolidation_counter = Counter(
    'consolidations_total',
    'Total de consolidações'
)

processing_time = Histogram(
    'processing_seconds',
    'Tempo de processamento'
)
```

---

## Versionamento

Ao fazer alterações, atualize `__version__`:

```python
# No início de app.py
__version__ = "1.0.0"
st.write(f"v{__version__}")
```

Tag releases:
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## Suporte

Para dúvidas:
1. Abra uma [Issue](https://github.com/seu-usuario/integrador-financeiro/issues)
2. Consulte a [Discussão](https://github.com/seu-usuario/integrador-financeiro/discussions)
3. Envie um [Pull Request](https://github.com/seu-usuario/integrador-financeiro/pulls)

---

**Última atualização:** 2024
