# 🚀 INÍCIO RÁPIDO

## 30 Segundos para começar

### 1. Instalar
```bash
pip install -r requirements.txt
```

### 2. Executar Streamlit
```bash
streamlit run app.py
```

### 3. Usar
- Carregue os 3 arquivos CSV/XLSX
- Clique "Consolidar Dados"
- Baixe o resultado

---

## Alternativa: Linha de Comando

```bash
python main.py matera.csv complementar.csv template.xlsx saida.xlsx
```

---

## Alternativa: Python Script

```python
from processor import process_integration, export_to_excel

result = process_integration(
    'Titulos_em_aberto_Matera.csv',
    'Título_em_Aberto.csv',
    'CR_MAXIFROTA_2026.xlsx'
)

export_to_excel(result, 'consolidado.xlsx')
```

---

## Arquivo

| Arquivo | Descrição |
|---------|-----------|
| **app.py** | 🎨 Interface Streamlit |
| **processor.py** | ⚙️ Lógica de dados |
| **main.py** | 🖥️ Execução CLI |
| **requirements.txt** | 📦 Dependências |
| **README.md** | 📖 Documentação completa |
| **CONFIGURACAO.md** | 🛠️ Deploy e setup |
| **EXEMPLOS.md** | 📚 Exemplos de uso |

---

## Problemas Comuns

**Erro: "Arquivo não encontrado"**
→ Certifique-se que os CSVs estão no mesmo diretório

**Erro: "UnicodeDecodeError"**
→ Os arquivos usam encoding `iso-8859-1`

**Erro: "Módulo não encontrado"**
→ Execute: `pip install -r requirements.txt`

---

## Próximos Passos

1. Leia [README.md](README.md) para detalhes técnicos
2. Veja [EXEMPLOS.md](EXEMPLOS.md) para casos de uso
3. Consulte [CONFIGURACAO.md](CONFIGURACAO.md) para deploy

---

**Tempo total:** ⚡ 2 minutos até o primeiro consolidado
