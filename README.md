# 🏦 Integrador Financeiro

Ferramenta corporativa de conciliação inteligente de títulos financeiros — integrando **Matera**, **Títulos em Aberto** e **CR Maxifrota 2026**.

---

## 🚀 Plataforma

| Ambiente | URL |
|----------|-----|
| **Produção (Render)** | `https://integrador-financeiro.onrender.com` |

---

## 📋 Funcionalidades

- **Upload de 3 arquivos**: Matera (CSV), Títulos em Aberto (CSV) e CR Maxifrota 2026 (XLSX)
- **Conciliação automática**: Cruzamento por número de documento normalizado
- **Classificação inteligente**: Títulos validados, a revisar ou apenas no Matera
- **Exportação Excel**: Download do resultado consolidado
- **Interface corporativa**: Design moderno com sidebar escura e métricas em tempo real
- **Diagnóstico completo**: Informações técnicas para troubleshooting

---

## 📦 Deploy no Render.com

### Configuração automática (recomendado)

O arquivo `render.yaml` na raiz configura automaticamente:

- **Tipo**: Web Service
- **Runtime**: Docker
- **Plano**: Free (0.1 vCPU, 512 MB RAM)
- **Porta**: Dinâmica via `$PORT`

### Deploy manual

1. Acesse [render.com](https://render.com)
2. Clique em **New +** → **Web Service**
3. Conecte o repositório GitHub
4. Configure:
   - **Runtime**: Docker
   - **Build Command**: (vazio, usa Dockerfile)
   - **Start Command**: (vazio, usa CMD do Dockerfile)
5. Clique em **Create Web Service**

---

## 🐳 Execução local com Docker

```bash
# Build da imagem
docker build -t integrador-financeiro .

# Executar (porta 8501)
docker run -p 8501:8501 integrador-financeiro

# Acessar
open http://localhost:8501
```

---

## 💻 Desenvolvimento local

```bash
# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Executar
streamlit run app.py
```

---

## 📁 Estrutura do Projeto

```
├── app.py                  # Aplicação Streamlit (interface web)
├── processor.py            # Motor de processamento (lógica de negócio)
├── Dockerfile              # Container Docker
├── render.yaml             # Configuração de deploy no Render.com
├── requirements.txt        # Dependências Python
├── .streamlit/
│   └── config.toml         # Configuração do Streamlit
├── .gitignore
├── .dockerignore
├── README.md               # Documentação principal
├── CONFIGURACAO.md         # Guia detalhado de configuração
└── INDEX.md                # Índice de documentação
```

---

## 📊 Fluxo de Processamento

```
┌──────────┐    ┌──────────────────┐    ┌────────────────┐
│  Matera  │    │ Títulos em Aberto │    │ CR Maxifrota   │
│  (CSV)   │    │      (CSV)        │    │    (XLSX)      │
└────┬─────┘    └────────┬─────────┘    └───────┬────────┘
     │                   │                      │
     └───────────────────┼──────────────────────┘
                         │
                    ┌────▼────┐
                    │ Process │
                    │ Engine  │
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼──┐ ┌────▼──┐ ┌────▼──┐
         │  OK   │ │Revisar│ │ Matera│
         │  CR   │ │        │ │ Only  │
         └───────┘ └───────┘ └───────┘
```

---

## 🔒 Privacidade

Todo o processamento é feito em memória (arquivos temporários). Nenhum dado é persistido em disco ou enviado a servidores externos.

---

## 📝 Requisitos dos Arquivos

| Arquivo | Formato | Coluna Obrigatória |
|---------|---------|--------------------|
| Matera | CSV | `sNumDocumento` |
| Títulos em Aberto | CSV | `NUM DOC MATERA` |
| CR Maxifrota 2026 | XLSX | `NUM DOC` |

---

## 🛠️ Tecnologias

- **Python 3.11+**
- **Streamlit 1.42+**
- **Pandas 2.x**
- **OpenPyXL** (leitura/escrita Excel)
- **Docker** (containerização)
- **Render.com** (deploy cloud)

---

© 2026 Integrador Financeiro. Todos os direitos reservados.