# Integrador de Planilhas Financeiras

Automação para consolidação de dados financeiros com validação de integridade, normalização de chaves e preenchimento de template obrigatório.

## 📋 Visão Geral

Este projeto integra três fontes de dados financeiras:
1. **Titulos em aberto Matera.csv** → Fonte de Verdade
2. **Título em Aberto.csv** → Fonte Complementar
3. **CR MAXIFROTA 2026.xlsx** → Template de Saída (layout obrigatório)

### Regras de Negócio
- Dados do Matera sempre prevalecem
- Campos sem correspondência são preenchidos com "REVISAR"
- Normalização de documentos: remove caracteres não numéricos antes de vincular
- Saída respeita exatamente as colunas do template

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- pip

### Setup Local

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/integrador-financeiro.git
cd integrador-financeiro

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## 💻 Como Usar

### Via Streamlit (Recomendado)

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

**Passos:**
1. Carregue os 3 arquivos CSV/XLSX
2. Clique em "Consolidar Dados"
3. Baixe o resultado em Excel ou CSV

### Via Python Script

```python
from processor import process_integration, export_to_excel

# Processar arquivos
result = process_integration(
    matera_path='Titulos_em_aberto_Matera.csv',
    complementar_path='Título_em_Aberto.csv',
    template_path='CR_MAXIFROTA_2026.xlsx'
)

# Exportar resultado
export_to_excel(result, 'consolidado.xlsx')

print(f"Processados {len(result)} registros")
```

## 📊 Estrutura do Projeto

```
.
├── app.py                          # Aplicação Streamlit
├── processor.py                    # Lógica de dados
├── requirements.txt                # Dependências
├── README.md                       # Este arquivo
└── .gitignore                      # Git ignore
```

## 🔧 Módulos

### `processor.py`

**Funções principais:**

#### `normalize_doc(valor)`
Normaliza número de documento removendo caracteres não numéricos.

```python
normalize_doc("4663656414.")  # "4663656414"
normalize_doc("46636564140")  # "46636564140"
```

#### `read_matera(filepath)`
Lê arquivo Matera e normaliza estrutura.

```python
df = read_matera('Titulos_em_aberto_Matera.csv')
```

#### `read_complementar(filepath)`
Lê arquivo complementar e padroniza colunas.

```python
df = read_complementar('Título_em_Aberto.csv')
```

#### `read_template(filepath)`
Obtém estrutura de colunas do template Excel.

```python
template = read_template('CR_MAXIFROTA_2026.xlsx')
```

#### `merge_data(matera, complementar)`
Consolida dados baseado em documento normalizado. Matera prevaleça.

```python
merged = merge_data(df_matera, df_complementar)
```

#### `fill_template(merged, template)`
Preenche template com dados consolidados.

```python
result = fill_template(merged, template)
```

#### `process_integration(matera_path, complementar_path, template_path)`
Executa fluxo completo.

```python
result = process_integration(
    'matera.csv',
    'complementar.csv',
    'template.xlsx'
)
```

#### `process_from_bytes(matera_bytes, complementar_bytes, template_bytes)`
Integração a partir de bytes (usado pelo Streamlit).

```python
result = process_from_bytes(bytes1, bytes2, bytes3)
```

#### `export_to_excel(df, output_path)`
Salva DataFrame em arquivo Excel.

```python
export_to_excel(result, 'output.xlsx')
```

#### `export_to_bytes(df)`
Retorna Excel em memória (bytes).

```python
excel_bytes = export_to_bytes(result)
```

### `app.py`

Interface Streamlit com:
- Upload de 3 arquivos
- Botão de consolidação
- Visualização prévia
- Download em Excel/CSV
- Métricas de processamento

## 📈 Fluxo de Dados

```
Matera.csv ──┐
             ├──> Normalizar ──┐
Complementar ┤                 ├──> Merge ──> Fill Template ──> Excel
             │                 │
Template.xlsx┴──────────────────┘
```

## 🔍 Validação e Tratamento de Erros

- **Documentos duplicados**: Dados Matera prevalecem
- **Campos faltantes**: Preenchidos com "REVISAR"
- **Dados inconsistentes**: Log de divergências na memória
- **Falha de leitura**: Mensagem de erro clara ao usuário

## 📝 Exemplo de Uso Completo

```python
from processor import (
    normalize_doc,
    read_matera,
    read_complementar,
    read_template,
    merge_data,
    fill_template,
    export_to_excel
)

# 1. Normalizar documento
doc = normalize_doc("4663656414.")
print(doc)  # "4663656414"

# 2. Ler arquivos
matera = read_matera('Titulos_em_aberto_Matera.csv')
complementar = read_complementar('Título_em_Aberto.csv')
template = read_template('CR_MAXIFROTA_2026.xlsx')

# 3. Consolidar
merged = merge_data(matera, complementar)

# 4. Preencher template
result = fill_template(merged, template)

# 5. Exportar
export_to_excel(result, 'consolidado.xlsx')

# 6. Estatísticas
print(f"Total: {len(result)} registros")
print(f"Colunas: {list(result.columns)}")
print(f"Campos REVISAR: {(result == 'REVISAR').sum().sum()}")
```

## 🔄 GitHub Actions (CI/CD)

Exemplo de workflow para validar:

```yaml
name: Test Integration

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/
```

## 🐛 Troubleshooting

### Erro: "Arquivo não encontrado"
Verifique caminhos dos arquivos e codificação (UTF-8).

### Erro: "Separador inválido"
Matera usa `;` (ponto-e-vírgula), complementar também usa `;`.

### Campos vazios no resultado
Significa que não houve correspondência. Verifique normalização:
```python
from processor import normalize_doc
normalize_doc("4663656414")  # Deve retornar "4663656414"
```

### Streamlit não carrega
```bash
pip install --upgrade streamlit
streamlit run app.py --logger.level=debug
```

## 📊 Colunas Esperadas

### Matera
dtReferencia, sEmpresa, sFilial, sReferencia, sCliente, sTipoDoc, sNumDocumento, dtEmissao, dtVctoOrig, dtUltVcto, nVlrParcela, sBanco, nVlrPendParcela, sIndVendor

### Complementar
RBASE, NOME CLIENTE, NOME, CNPJ, UF, TIPO, PRODUTO, DT EMISSAO, DT VENCIMENTO, NUM DOC MATERA, VLR SALDO, VLR TITULO, IR RETIDO, ISS RETIDO, CSLL RETIDO, COFINS, PIS, EXECUTIVO, DATA BLOQUEIO, ATRASO, COND PAGTO, NR NFEM, EMPRESA, SISTEMA, PORTADOR, LINK NFSE, RBASE RAIZ, CIDADE

### Template (Saída)
EMPRESA, EXECUTIVO, PRODUTO, CNPJ, RBASE, NF, NUM DOC, CLIENTE, CLIENTE 2, UF, CIDADE, GRUPO, TIPO, COND PAGTO, DT EMISSAO, DT VENCIMENTO, VLR TITULO, VLR SALDO, IR, ISS, LIQUIDO CORRETO, PAGA NA DATA, RISCO DE INADIMPLÊNCIA, CREDIT SCORE, SCORE CLASS, PROB DEFAULT (%), TENDÊNCIA, PREVISAO DE PAGAMENTO, BANCO, DATA BLOQUEIO, CODIGO PAGAMENTO, ATRASO, LINK NFSE, SISTEMA, RBASE RAIZ

## 🤝 Contribuindo

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/melhoria`)
3. Commit mudanças (`git commit -am 'Add feature'`)
4. Push para a branch (`git push origin feature/melhoria`)
5. Abra um Pull Request

## 📄 Licença

MIT License - veja LICENSE para detalhes.

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

---

**Última atualização:** 2024
