FROM python:3.9-slim

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Expor porta
EXPOSE 8501

# Comando de inicialização
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--logger.level=error"]
