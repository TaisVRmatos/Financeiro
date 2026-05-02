import pandas as pd
import numpy as np
from typing import Optional, Any, List, Set, Tuple
import io
import openpyxl  # noqa: F401 - garante engine para pd.read_excel


def normalize_doc(valor: Any) -> Optional[str]:
    """
    Normaliza número de documento removendo caracteres não numéricos.

    Args:
        valor: Valor a normalizar (pode ser string, int, float ou NaN)

    Returns:
        String contendo apenas dígitos ou None se valor for vazio
    """
    if pd.isna(valor):
        return None
    return ''.join(filter(str.isdigit, str(valor)))


# ---------------------------------------------------------------------------
# MAPEAMENTO: coluna do resultado  ->  [fonte Matera, fonte Complementar]
# Usado APENAS para títulos que NÃO possuem match no CR Maxifrota
# (existem só no Matera, não nos Títulos em Aberto)
# ---------------------------------------------------------------------------
COLUMN_MAPPING: dict = {
    'EMPRESA':                 ['sEmpresa',               'EMPRESA'],
    'EXECUTIVO':               ['EXECUTIVO',              'EXECUTIVO'],
    'PRODUTO':                 ['PRODUTO',                'PRODUTO'],
    'CNPJ':                    ['CNPJ',                   'CNPJ'],
    'RBASE':                   ['RBASE',                  'RBASE'],
    'NF':                      ['NR NFEM',                'NR NFEM'],
    'NUM DOC':                 ['sNumDocumento',          'NUM DOC MATERA'],
    'CLIENTE':                 ['sCliente',               'NOME CLIENTE'],
    'CLIENTE 2':               ['sCliente',               'NOME CLIENTE'],
    'UF':                      ['UF',                     'UF'],
    'CIDADE':                  ['CIDADE',                 'CIDADE'],
    'GRUPO':                   ['GRUPO',                  'GRUPO'],
    'TIPO':                    ['TIPO',                    'TIPO'],
    'COND PAGTO':              ['COND PAGTO',             'COND PAGTO'],
    'DT EMISSAO':              ['dtEmissao',              'DT EMISSAO'],
    'DT VENCIMENTO':           ['dtUltVcto',              'DT VENCIMENTO'],
    'VLR TITULO':              ['nVlrParcela',            'VLR TITULO'],
    'VLR SALDO':               ['nVlrPendParcela',        'VLR SALDO'],
    'IR':                      ['IR RETIDO',              'IR RETIDO'],
    'ISS':                     ['ISS RETIDO',             'ISS RETIDO'],
    'LIQUIDO CORRETO':         ['CSLL RETIDO',            'CSLL RETIDO'],
    'PAGA NA DATA':            ['COFINS',                 'COFINS'],
    'RISCO DE INADIMPLÊNCIA':  ['PIS',                    'PIS'],
    'CREDIT SCORE':            ['CREDIT SCORE',           'CREDIT SCORE'],
    'SCORE CLASS':             [],
    'PROB DEFAULT (%)':        [],
    'TENDÊNCIA':               [],
    'PREVISAO DE PAGAMENTO':   [],
    'BANCO':                   ['sBanco',                 'BANCO'],
    'DATA BLOQUEIO':           ['DATA BLOQUEIO',          'DATA BLOQUEIO'],
    'CODIGO PAGAMENTO':        [],
    'ATRASO':                  ['ATRASO',                 'ATRASO'],
    'LINK NFSE':               ['LINK NFSE',              'LINK NFSE'],
    'SISTEMA':                 ['SISTEMA',                'SISTEMA'],
    'RBASE RAIZ':              ['RBASE RAIZ',             'RBASE RAIZ'],
}


# ---------------------------------------------------------------------------
# ENCODINGS comuns para tentar em ordem
# ---------------------------------------------------------------------------
_ENCODINGS = ['utf-8', 'iso-8859-1', 'latin-1', 'cp1252', 'utf-8-sig']

# ---------------------------------------------------------------------------
# Colunas obrigatórias em cada arquivo (nome_arquivo -> [colunas])
# ---------------------------------------------------------------------------
_REQUIRED_COLUMNS = {
    'Matera': ['sNumDocumento'],
    'Títulos em Aberto': ['NUM DOC MATERA'],
    'CR MAXIFROTA 2026': ['NUM DOC'],
}


def _detect_encoding_sep(csv_bytes: bytes, nome_arquivo: str) -> Tuple[str, pd.DataFrame]:
    """
    Tenta ler um CSV com diferentes combinações de encoding e separador.
    Retorna (separador_detectado, DataFrame).

    Lança ValueError com mensagem clara se nenhuma combinação funcionar.
    """
    erros: list = []

    for enc in _ENCODINGS:
        for sep in [';', ',']:
            try:
                df = pd.read_csv(
                    io.BytesIO(csv_bytes),
                    sep=sep,
                    encoding=enc,
                    on_bad_lines='skip',
                )
                # Se leu com mais de 1 coluna, considera sucesso
                if len(df.columns) > 1:
                    return sep, df
            except Exception as e:
                erros.append(f"  encoding={enc}, separador='{sep}': {e}")

    # Tenta última chance: sniff com csv.Sniffer (ignora encoding)
    try:
        import csv
        texto = csv_bytes.decode('utf-8', errors='replace')
        dialect = csv.Sniffer().sniff(texto[:10000])
        sep = dialect.delimiter
        for enc in _ENCODINGS:
            try:
                df = pd.read_csv(io.BytesIO(csv_bytes), sep=sep, encoding=enc)
                if len(df.columns) > 1:
                    return sep, df
            except Exception:
                pass
    except Exception:
        pass

    raise ValueError(
        f"❌ Arquivo **{nome_arquivo}**: não foi possível ler o CSV.\n\n"
        f"Formatos tentados (encoding × separador): {len(_ENCODINGS) * 2} combinações\n"
        f"Verifique se o arquivo é realmente um CSV válido e não está corrompido.\n\n"
        f"Detalhes:\n" + "\n".join(erros[-6:])
    )


def _validate_columns(df: pd.DataFrame, nome_arquivo: str) -> None:
    """
    Valida se as colunas obrigatórias existem no DataFrame.
    Lança ValueError com mensagem clara se faltar alguma coluna.

    Também faz strip nos nomes das colunas para evitar problemas de espaços.
    """
    df.columns = df.columns.str.strip()
    colunas_obrigatorias = _REQUIRED_COLUMNS.get(nome_arquivo, [])

    faltando = [c for c in colunas_obrigatorias if c not in df.columns]

    if faltando:
        colunas_encontradas = ', '.join(df.columns[:20].tolist())
        if len(df.columns) > 20:
            colunas_encontradas += f' ... (+{len(df.columns) - 20} colunas)'

        raise ValueError(
            f"❌ Arquivo **{nome_arquivo}**: coluna(s) obrigatória(s) não encontrada(s):\n"
            f"   **{', '.join(faltando)}**\n\n"
            f"   Colunas encontradas no arquivo:\n"
            f"   {colunas_encontradas}\n\n"
            f"   💡 Verifique se o arquivo enviado é o correto."
        )


def _safe_value(series: pd.Series, idx: int) -> Any:
    """Obtém valor seguro de uma Series, retornando None para NaN/NaT."""
    try:
        val = series.iloc[idx] if hasattr(series, 'iloc') else series[idx]
        if pd.isna(val):
            return None
        return val
    except (IndexError, KeyError):
        return None


def _get_column_value(df: pd.DataFrame, col_name: str, idx: int) -> Any:
    """Obtém valor de uma coluna específica pelo índice. None se coluna não existir."""
    if col_name in df.columns:
        return _safe_value(df[col_name], idx)
    return None


def _collect_all_columns(
    matera: pd.DataFrame,
    complementar: pd.DataFrame,
    cr_maxifrota: pd.DataFrame
) -> List[str]:
    """
    Coleta a UNIÃO de todas as colunas das 3 planilhas,
    excluindo a coluna auxiliar 'doc_normalized'.

    A ordem é: colunas do CR primeiro, depois colunas do Matera não
    duplicadas, depois colunas do Complementar não duplicadas.
    """
    seen: Set[str] = set()
    result: List[str] = []

    # CR Maxifrota primeiro (define layout principal)
    for col in cr_maxifrota.columns:
        if col != 'doc_normalized' and col not in seen:
            result.append(col)
            seen.add(col)

    # Matera
    for col in matera.columns:
        if col != 'doc_normalized' and col not in seen:
            result.append(col)
            seen.add(col)

    # Complementar (Títulos em Aberto)
    for col in complementar.columns:
        if col != 'doc_normalized' and col not in seen:
            result.append(col)
            seen.add(col)

    return result


def _build_row_from_cr(
    cr_row: pd.Series,
    all_columns: List[str],
) -> dict:
    """Constrói um dicionário de linha a partir de uma linha do CR Maxifrota."""
    row = {}
    for col in all_columns:
        if col in cr_row.index:
            row[col] = cr_row[col]  # preserva tipo original (int/float/str/NaN)
        else:
            row[col] = None
    row['AUXILIAR'] = 'OK - Validado (CR Maxifrota)'
    return row


def _build_row_from_matera(
    matera: pd.DataFrame,
    idx: int,
    all_columns: List[str],
    auxiliar_msg: str,
) -> dict:
    """
    Constrói um dicionário de linha a partir do Matera usando
    COLUMN_MAPPING para traduzir nomes de colunas.

    Colunas que não estão no mapeamento são preenchidas como vazias.
    Colunas do CR que existem no Matera com nome diferente são mapeadas.
    Colunas exclusivas do Matera (fora do mapeamento) são copiadas diretamente.
    """
    row = {}
    for col in all_columns:
        if col in COLUMN_MAPPING:
            matera_src = COLUMN_MAPPING[col][0] if len(COLUMN_MAPPING[col]) > 0 else None
            if matera_src:
                val = _get_column_value(matera, matera_src, idx)
                row[col] = val  # preserva tipo original (None = NaN)
            else:
                row[col] = None
        elif col in matera.columns:
            val = _get_column_value(matera, col, idx)
            row[col] = val  # preserva tipo original
        else:
            row[col] = None
    row['AUXILIAR'] = auxiliar_msg
    return row


def sanitize_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garante que todas as colunas tenham tipos compatíveis com PyArrow/Streamlit.
    - Colunas numéricas → float64 (NaN preenchido com 0)
    - Colunas de data → datetime64 (NaT preenchido com None)
    - Demais colunas → string (NaN preenchido com '')
    """
    df = df.copy()

    for col in df.columns:
        series = df[col]

        # Se já é numérico, preenche NaN com 0
        if pd.api.types.is_numeric_dtype(series):
            df[col] = series.fillna(0)
            continue

        # Se já é datetime, mantém
        if pd.api.types.is_datetime64_any_dtype(series):
            continue

        # Se é booleano, converte para string
        if pd.api.types.is_bool_dtype(series):
            df[col] = series.fillna(False).astype(str)
            continue

        # Para object e outros: tenta converter para numérico primeiro
        try:
            numeric = pd.to_numeric(series, errors='raise')
            df[col] = numeric.fillna(0).astype('float64')
            continue
        except (ValueError, TypeError):
            pass

        # Tenta converter para datetime
        try:
            dt = pd.to_datetime(series, errors='raise')
            df[col] = dt
            continue
        except (ValueError, TypeError):
            pass

        # Fallback: converte tudo para string, NaN → ''
        df[col] = series.fillna('').astype(str)

    return df


def _build_result(
    matera: pd.DataFrame,
    complementar: pd.DataFrame,
    cr_maxifrota: pd.DataFrame,
) -> pd.DataFrame:
    """
    Constrói o DataFrame final aplicando as regras de negócio:

    1. Títulos que existem no Matera E nos Títulos em Aberto:
       → Preenchidos com dados do CR Maxifrota 2026, mantendo
         TODAS as colunas do CR.

    2. Títulos que existem APENAS no Matera:
       → Preenchidos com dados do Matera.

    3. Títulos que existem APENAS nos Títulos em Aberto:
       → EXCLUÍDOS (não aparecem no resultado).

    As colunas do resultado final são a UNIÃO de todas as colunas
    das 3 planilhas (CR + Matera + Títulos em Aberto).
    """
    # Coletar união de todas as colunas
    all_columns = _collect_all_columns(matera, complementar, cr_maxifrota)

    # Conjuntos de docs normalizados
    docs_matera = set(matera['doc_normalized'].dropna())
    docs_complementar = set(complementar['doc_normalized'].dropna())
    docs_cr = set(cr_maxifrota['doc_normalized'].dropna())

    # Docs que existem no Matera E no Títulos em Aberto (validados)
    docs_validados = docs_matera & docs_complementar

    # Docs que existem APENAS no Matera
    docs_apenas_matera = docs_matera - docs_complementar

    # Docs que existem APENAS no Títulos em Aberto → EXCLUÍDOS (ignorar)

    # Índice do CR por doc_normalized
    cr_indexed = cr_maxifrota.set_index('doc_normalized')

    result_rows = []

    # Grupo 1: Títulos validados (Matera + Títulos em Aberto)
    for doc in sorted(docs_validados):
        if doc in cr_indexed.index:
            cr_row = cr_indexed.loc[doc]
            if isinstance(cr_row, pd.DataFrame):
                cr_row = cr_row.iloc[0]
            row = _build_row_from_cr(cr_row, all_columns)
        else:
            # Existe nas 2 fontes mas NÃO no CR → preencher do Matera
            matera_match = matera[matera['doc_normalized'] == doc]
            if len(matera_match) > 0:
                idx = matera_match.index[0]
                row = _build_row_from_matera(
                    matera, idx, all_columns,
                    'REVISAR - Nos Títulos em Aberto mas NÃO no CR Maxifrota'
                )
            else:
                continue
        result_rows.append(row)

    # Grupo 2: Títulos apenas no Matera
    for doc in sorted(docs_apenas_matera):
        matera_match = matera[matera['doc_normalized'] == doc]
        if len(matera_match) > 0:
            idx = matera_match.index[0]
            row = _build_row_from_matera(
                matera, idx, all_columns,
                'Apenas Matera - Sem correspondência nos Títulos em Aberto'
            )
            result_rows.append(row)

    # Consolidar
    if result_rows:
        result = pd.DataFrame(result_rows, columns=all_columns + ['AUXILIAR'])
    else:
        result = pd.DataFrame(columns=all_columns + ['AUXILIAR'])

    # Converter colunas numéricas para tipo correto (evitar object dtype)
    for col in all_columns:
        if col in result.columns:
            # Tenta converter para numérico, ignorando erros
            result[col] = pd.to_numeric(result[col], errors='ignore')

    return result


def process_integration(
    matera_path: str,
    complementar_path: str,
    cr_maxifrota_path: str
) -> pd.DataFrame:
    """
    Executa fluxo completo de integração a partir de caminhos de arquivo.

    Args:
        matera_path: Caminho arquivo Matera (CSV)
        complementar_path: Caminho arquivo Títulos em Aberto (CSV)
        cr_maxifrota_path: Caminho arquivo CR MAXIFROTA 2026 (XLSX)

    Returns:
        DataFrame consolidado + coluna AUXILIAR
    """
    matera = _read_matera(matera_path)
    complementar = _read_complementar(complementar_path)
    cr_maxifrota = _read_cr_maxifrota(cr_maxifrota_path)

    result = _build_result(matera, complementar, cr_maxifrota)
    return result


def process_from_bytes(
    matera_bytes: bytes,
    complementar_bytes: bytes,
    cr_maxifrota_bytes: bytes
) -> pd.DataFrame:
    """
    Executa integração a partir de bytes (para Streamlit).

    Faz detecção automática de encoding e separador nos CSVs.
    Valida colunas obrigatórias com mensagens claras de erro.

    Args:
        matera_bytes: Conteúdo arquivo Matera em bytes
        complementar_bytes: Conteúdo arquivo Títulos em Aberto em bytes
        cr_maxifrota_bytes: Conteúdo arquivo CR MAXIFROTA 2026 em bytes

    Returns:
        DataFrame consolidado + coluna AUXILIAR

    Raises:
        ValueError: se arquivo CSV inválido, encoding não reconhecido
                    ou colunas obrigatórias faltando
    """
    # --- Ler Matera (CSV) ---
    _sep_matera, matera = _detect_encoding_sep(matera_bytes, 'Matera')
    _validate_columns(matera, 'Matera')
    matera = matera.dropna(axis=1, how='all')
    matera['doc_normalized'] = matera['sNumDocumento'].apply(normalize_doc)

    # --- Ler Títulos em Aberto (CSV) ---
    _sep_comp, complementar = _detect_encoding_sep(
        complementar_bytes, 'Títulos em Aberto'
    )
    _validate_columns(complementar, 'Títulos em Aberto')
    complementar.columns = complementar.columns.str.strip()
    complementar = complementar.dropna(axis=1, how='all')
    complementar['doc_normalized'] = complementar['NUM DOC MATERA'].apply(normalize_doc)

    # --- Ler CR Maxifrota (XLSX) ---
    try:
        cr_maxifrota = pd.read_excel(io.BytesIO(cr_maxifrota_bytes), engine='openpyxl')
    except Exception as e:
        raise ValueError(
            f"❌ Arquivo **CR MAXIFROTA 2026**: não foi possível ler o Excel.\n\n"
            f"Erro: {e}\n\n"
            f"💡 O arquivo deve estar no formato .xlsx (Excel 2007+). "
            f"Verifique se não é .xls antigo ou arquivo corrompido."
        ) from e
    _validate_columns(cr_maxifrota, 'CR MAXIFROTA 2026')
    cr_maxifrota = cr_maxifrota.dropna(axis=1, how='all')
    cr_maxifrota['doc_normalized'] = cr_maxifrota['NUM DOC'].apply(normalize_doc)

    return _build_result(matera, complementar, cr_maxifrota)


def _read_matera(filepath: str) -> pd.DataFrame:
    """Lê arquivo Matera CSV."""
    df = pd.read_csv(filepath, sep=';', encoding='iso-8859-1')
    df = df.dropna(axis=1, how='all')
    df['doc_normalized'] = df['sNumDocumento'].apply(normalize_doc)
    return df


def _read_complementar(filepath: str) -> pd.DataFrame:
    """Lê arquivo Títulos em Aberto CSV."""
    df = pd.read_csv(filepath, sep=';', encoding='iso-8859-1')
    df.columns = df.columns.str.strip()
    df = df.dropna(axis=1, how='all')
    df['doc_normalized'] = df['NUM DOC MATERA'].apply(normalize_doc)
    return df


def _read_cr_maxifrota(filepath: str) -> pd.DataFrame:
    """Lê planilha CR MAXIFROTA 2026 XLSX."""
    df = pd.read_excel(filepath)
    df = df.dropna(axis=1, how='all')
    df['doc_normalized'] = df['NUM DOC'].apply(normalize_doc)
    return df


def export_to_excel(df: pd.DataFrame, output_path: str) -> None:
    """Exporta DataFrame para arquivo Excel."""
    df.to_excel(output_path, index=False, sheet_name='Consolidado')


def export_to_bytes(df: pd.DataFrame) -> bytes:
    """Exporta DataFrame para bytes (Excel em memória)."""
    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name='Consolidado', engine='openpyxl')
    output.seek(0)
    return output.getvalue()