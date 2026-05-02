# 📚 EXEMPLOS DE USO

## 1. Execução via Streamlit (Recomendado)

```bash
streamlit run app.py
```

Então:
1. Carregue os 3 arquivos CSV/XLSX
2. Clique "Consolidar Dados"
3. Visualize a prévia
4. Baixe em Excel ou CSV

---

## 2. Execução via Script Python

### Opção A: Usando main.py
```bash
# Uso básico
python main.py Titulos_em_aberto_Matera.csv "Título_em_Aberto.csv" CR_MAXIFROTA_2026.xlsx

# Com saída customizada
python main.py matera.csv complementar.csv template.xlsx meu_resultado.xlsx

# Com detalhes de execução
python main.py matera.csv complementar.csv template.xlsx resultado.xlsx --verbose
```

### Opção B: Usando processor.py
```python
from processor import process_integration, export_to_excel

# Processar
result = process_integration(
    'Titulos_em_aberto_Matera.csv',
    'Título_em_Aberto.csv',
    'CR_MAXIFROTA_2026.xlsx'
)

# Exportar
export_to_excel(result, 'consolidado.xlsx')

# Informações
print(f"Processados: {len(result)} registros")
print(f"Colunas: {len(result.columns)}")
```

---

## 3. Usando em Jupyter Notebook

```python
import pandas as pd
from processor import (
    read_matera,
    read_complementar,
    read_template,
    merge_data,
    fill_template,
    export_to_excel
)

# 1. Ler dados
matera = read_matera('Titulos_em_aberto_Matera.csv')
complementar = read_complementar('Título_em_Aberto.csv')
template = read_template('CR_MAXIFROTA_2026.xlsx')

print(f"Matera: {len(matera)} registros")
print(f"Complementar: {len(complementar)} registros")

# 2. Consolidar
merged = merge_data(matera, complementar)
print(f"Consolidado: {len(merged)} registros")

# 3. Preencher template
result = fill_template(merged, template)
print(f"Resultado final: {len(result)} registros")

# 4. Visualizar
display(result.head(10))

# 5. Analisar qualidade
revisar_count = (result.astype(str) == 'REVISAR').sum().sum()
print(f"Campos REVISAR: {revisar_count}")

# 6. Exportar
export_to_excel(result, 'consolidado.xlsx')
```

---

## 4. Processando Bytes (Para APIs)

```python
from processor import process_from_bytes, export_to_bytes

# Ler arquivos
with open('matera.csv', 'rb') as f:
    matera_bytes = f.read()

with open('complementar.csv', 'rb') as f:
    complementar_bytes = f.read()

with open('template.xlsx', 'rb') as f:
    template_bytes = f.read()

# Processar
result = process_from_bytes(matera_bytes, complementar_bytes, template_bytes)

# Exportar para bytes (sem salvar em disco)
output_bytes = export_to_bytes(result)

# Usar output_bytes para enviar via HTTP, S3, etc
print(f"Excel em memória: {len(output_bytes)} bytes")
```

---

## 5. Normalização de Documentos

```python
from processor import normalize_doc

# Exemplos
docs = [
    "4663656414",      # Já normalizado
    "4663656414.",     # Com ponto
    "4.663.656.414",   # Com formatação
    "4663-656-414",    # Com hífen
    None,              # Valor nulo
    "46636564140"      # Diferente
]

for doc in docs:
    normalized = normalize_doc(doc)
    print(f"{str(doc):20} → {normalized}")
```

Saída:
```
4663656414           → 4663656414
4663656414.          → 4663656414
4.663.656.414        → 4663656414
4663-656-414         → 4663656414
None                 → None
46636564140          → 46636564140
```

---

## 6. Validação de Dados

```python
import pandas as pd
from processor import read_matera, read_complementar

# Ler
matera = read_matera('Titulos_em_aberto_Matera.csv')
complementar = read_complementar('Título_em_Aberto.csv')

# Análise Matera
print("=== MATERA ===")
print(f"Total: {len(matera)}")
print(f"Documentos únicos: {matera['doc_normalized'].nunique()}")
print(f"Valores vazios por coluna:")
print(matera.isna().sum())

# Análise Complementar
print("\n=== COMPLEMENTAR ===")
print(f"Total: {len(complementar)}")
print(f"Documentos únicos: {complementar['doc_normalized'].nunique()}")
print(f"Valores vazios por coluna:")
print(complementar.isna().sum())

# Verificar cobertura
docs_matera = set(matera['doc_normalized'].dropna())
docs_complementar = set(complementar['doc_normalized'].dropna())

print(f"\n=== COBERTURA ===")
print(f"Docs apenas em Matera: {len(docs_matera - docs_complementar)}")
print(f"Docs em ambas: {len(docs_matera & docs_complementar)}")
print(f"Docs apenas em Complementar: {len(docs_complementar - docs_matera)}")
```

---

## 7. Exportando para Diferentes Formatos

```python
from processor import process_integration
import pandas as pd

result = process_integration(
    'matera.csv',
    'complementar.csv',
    'template.xlsx'
)

# Excel
result.to_excel('resultado.xlsx', index=False)

# CSV (com ponto-e-vírgula)
result.to_csv('resultado.csv', sep=';', encoding='utf-8', index=False)

# JSON
result.to_json('resultado.json', orient='records', force_ascii=False, indent=2)

# Parquet (mais eficiente)
result.to_parquet('resultado.parquet')

# SQL
import sqlite3
conn = sqlite3.connect('resultado.db')
result.to_sql('consolidado', conn, if_exists='replace', index=False)
conn.close()
```

---

## 8. Filtrando Dados Específicos

```python
from processor import process_integration

result = process_integration(
    'matera.csv',
    'complementar.csv',
    'template.xlsx'
)

# Apenas registros com REVISAR
revisar_df = result[result.astype(str).eq('REVISAR').any(axis=1)]
print(f"Registros com REVISAR: {len(revisar_df)}")

# Por cliente
cliente_df = result[result['CLIENTE'].str.contains('JOSÉ', na=False)]
print(f"Registros de JOSÉ: {len(cliente_df)}")

# Por período
result['DT EMISSAO'] = pd.to_datetime(result['DT EMISSAO'], errors='coerce')
janeiro = result[result['DT EMISSAO'].dt.month == 1]
print(f"Registros de janeiro: {len(janeiro)}")

# Com valor > 1000
result['VLR TITULO'] = pd.to_numeric(result['VLR TITULO'], errors='coerce')
maiores = result[result['VLR TITULO'] > 1000]
print(f"Títulos maiores que 1000: {len(maiores)}")
```

---

## 9. Gerando Relatórios

```python
from processor import process_integration
import pandas as pd

result = process_integration(
    'matera.csv',
    'complementar.csv',
    'template.xlsx'
)

# Resumo por cliente
resumo_cliente = result.groupby('CLIENTE').agg({
    'NUM DOC': 'count',
    'VLR TITULO': ['sum', 'mean', 'max']
}).round(2)
print(resumo_cliente)

# Resumo por executivo
resumo_exec = result.groupby('EXECUTIVO').agg({
    'VLR SALDO': ['sum', 'count']
}).round(2)
print(resumo_exec)

# Resumo por UF
resumo_uf = result.groupby('UF').agg({
    'VLR TITULO': 'sum',
    'NUM DOC': 'count'
}).round(2)
print(resumo_uf)

# Salvar relatórios
with pd.ExcelWriter('relatorios.xlsx') as writer:
    resumo_cliente.to_excel(writer, sheet_name='Por Cliente')
    resumo_exec.to_excel(writer, sheet_name='Por Executivo')
    resumo_uf.to_excel(writer, sheet_name='Por UF')
```

---

## 10. Integração com Banco de Dados

```python
from processor import process_integration
import sqlite3

# Processar
result = process_integration(
    'matera.csv',
    'complementar.csv',
    'template.xlsx'
)

# Conectar ao banco
conn = sqlite3.connect('financeiro.db')

# Salvar tabela
result.to_sql('titulos_consolidados', conn, if_exists='replace', index=False)

# Consultas
import pandas as pd

# Total por cliente
query = """
    SELECT CLIENTE, COUNT(*) as qtd, SUM(VLR_TITULO) as total
    FROM titulos_consolidados
    GROUP BY CLIENTE
    ORDER BY total DESC
"""
df = pd.read_sql(query, conn)
print(df)

conn.close()
```

---

## 11. Testes Unitários

```bash
# Instalar pytest
pip install pytest pytest-cov

# Rodar todos os testes
pytest test_processor.py -v

# Com cobertura
pytest test_processor.py --cov=processor --cov-report=html

# Teste específico
pytest test_processor.py::TestNormalizeDoc::test_normalize_clean_number -v
```

---

## 12. Debugging e Logs

```python
import logging
from processor import process_integration

# Configurar logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('consolidacao.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Iniciando integração...")

try:
    result = process_integration(
        'matera.csv',
        'complementar.csv',
        'template.xlsx'
    )
    logger.info(f"Sucesso: {len(result)} registros processados")
except Exception as e:
    logger.error(f"Erro: {e}", exc_info=True)
```

---

## Dúvidas Frequentes

**P: Como alterar o separador dos CSVs?**
R: Edite `read_matera()` e `read_complementar()`, mude `sep=';'` para o separador desejado.

**P: Como usar outra codificação?**
R: Mude `encoding='iso-8859-1'` para a codificação desejada (ex: `'utf-8'`, `'cp1252'`).

**P: Posso processar arquivos grandes?**
R: Sim, usando chunks com Pandas: `pd.read_csv(..., chunksize=10000)`

**P: Como enviar o resultado por email?**
R: Use `smtplib` + `export_to_bytes()` para enviar sem salvar em disco.

---

**Última atualização:** 2024
