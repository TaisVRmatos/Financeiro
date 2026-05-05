# ⚙️ Guia de Configuração — Integrador Financeiro

Guia completo para configurar, customizar e fazer deploy do Integrador Financeiro no **Render.com**.

---

## 📦 1. Deploy no Render.com

### Pré-requisitos

- Conta no [Render.com](https://render.com) (plano gratuito)
- Repositório Git hospedado (GitHub recomendado)
- Docker (para testes locais)

### Opção A: Blueprint (render.yaml)

O arquivo `render.yaml` na raiz do projeto permite deploy com 1 clique:

1. No dashboard do Render, clique em **New +** → **Blueprint**
2. Conecte o repositório
3. O Render detecta automaticamente o `render.yaml` e cria o serviço

### Opção B: Deploy Manual

1. **New +** → **Web Service**
2. Conecte o repositório
3. Configure:
   - **Name**: `integrador-financeiro`
   - **Region**: `Oregon (US West)` — mais próxima do Brasil
   - **Runtime**: `Docker`
   - **Instance Type**: `Free`
4. Variáveis de ambiente (opcionais):
   - `PORT`: Gerenciada automaticamente pelo Render
   - `STREAMLIT_SERVER_ENABLE_CORS`: `false`
   - `STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION`: `false`
5. Clique em **Create Web Service**

### Primeiro Deploy

- O build inicial leva **3-5 minutos**
- Após o deploy, o Render fornece uma URL pública: `https://integrador-financeiro.onrender.com`
- **Atenção**: No plano gratuito, o serviço hiberna após 15 minutos de inatividade. O primeiro acesso após hibernação pode levar 30-60 segundos.

---

## 🐳 2. Configuração Docker

### Dockerfile

O Dockerfile já está configurado com todas as otimizações necessárias:

```dockerfile
FROM python:3.11-slim
# Multi-stage build otimizado para Render
```

### Build Local

```bash
docker build -t integrador-financeiro .
docker run -p 8501:8501 integrador-financeiro
```

---

## 🎨 3. Configuração Streamlit

### .streamlit/config.toml

```toml
[server]
port = 8501
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = false
headless = true

[browser]
serverAddress = "0.0.0.0"
gatherUsageStats = false

[theme]
primaryColor = "#2563eb"
backgroundColor = "#f0f4f8"
secondaryBackgroundColor = "#ffffff"
textColor = "#1e293b"
font = "sans serif"
```

### Porta Dinâmica no Render

O Render injeta a variável `$PORT` automaticamente. O `CMD` do Dockerfile lê essa variável:

```dockerfile
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Para testes locais, a porta padrão é `8501`.

---

## 📊 4. Configuração do Processamento

### Arquivos de Entrada

| Fonte | Formato | Coluna Chave | Encoding Esperado |
|-------|---------|--------------|-------------------|
| Matera | CSV | `sNumDocumento` | UTF-8 / Latin1 |
| Títulos em Aberto | CSV | `NUM DOC MATERA` | UTF-8 / Latin1 |
| CR Maxifrota | XLSX | `NUM DOC` | N/A |

### Tamanho Máximo de Upload

- **Padrão**: 200 MB (configurável em `.streamlit/config.toml`)
- **Plano Free Render**: Limite de memória 512 MB — mantenha arquivos abaixo de 100 MB

---

## 🔧 5. Variáveis de Ambiente

| Variável | Descrição | Padrão | Obrigatória |
|----------|-----------|--------|-------------|
| `PORT` | Porta do servidor (Render injeta automaticamente) | `8501` | Não |
| `STREAMLIT_SERVER_ENABLE_CORS` | CORS | `false` | Não |
| `STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION` | XSRF | `false` | Não |

---

## 🚨 6. Troubleshooting

### "Application failed to respond"

- Verifique se a aplicação está escutando na porta `$PORT`
- O Render espera resposta HTTP na porta dentro de 3 minutos após o build
- Veja os logs no dashboard do Render: **Logs** tab

### "File upload não funciona"

- Verifique `maxUploadSize` no `config.toml`
- Arquivos grandes podem exceder a memória do plano Free (512 MB)
- O bug do `st.form` com `st.file_uploader` foi corrigido — não use forms para upload

### Erro de processamento

- Verifique se as colunas obrigatórias estão presentes nos arquivos
- Confira o encoding dos CSVs (UTF-8 ou Latin1)
- Use a seção **Informações de Diagnóstico** na interface para detalhes

---

## 📈 7. Monitoramento

- **Render Dashboard**: Métricas de CPU, memória e banda
- **Logs**: Acessíveis via dashboard Render → seu serviço → **Logs**
- **Health Check**: Render verifica a rota `/healthz` a cada 30 segundos

---

## 🔄 8. CI/CD

### Deploy Automático (GitHub + Render)

1. No Render, ao conectar o repositório, ative **Auto Deploy**
2. Commits na branch principal (geralmente `main`) disparam deploy automaticamente
3. Builds subsequentes usam cache Docker para acelerar

### Webhook Manual

```bash
curl -X POST "https://api.render.com/deploy/srv-xxxxx?key=YOUR_DEPLOY_KEY"
```

---

## 📞 Suporte

Para problemas técnicos, abra uma issue no repositório ou contate a equipe de TI.

---

© 2026 Integrador Financeiro