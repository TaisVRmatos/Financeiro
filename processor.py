import pandas as pd
import numpy as np
from typing import Tuple, Optional, Any, List
import io


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


def read_matera(filepath: str) -> pd.DataFrame:
    """
    Lê arquivo Matera (FONTE DE VERDADE).

    Args:
        filepath: Caminho do arquivo CSV Matera

    Returns:
        DataFrame com dados Matera normalizados
    """
    df = pd.read_csv(filepath, sep=';', encoding='iso-8859-1')
    df = df.dropna(axis=1, how='all')
    df['doc_normalized'] = df['sNumDocumento'].apply(normalize_doc)
    return df


def read_complementar(filepath: str) -> pd.DataFrame:
    """
    Lê arquivo Títulos em Aberto (complementar).

    Args:
        filepath: Caminho do arquivo CSV complementar

    Returns:
        DataFrame com dados complementares normalizados
    """
    df = pd.read_csv(filepath, sep=';', encoding='iso-8859-1')
    df.columns = df.columns.str.strip()
    df = df.dropna(axis=1, how='all')
    df['doc_normalized'] = df['NUM DOC MATERA'].apply(normalize_doc)
    return df


def read_cr_maxifrota(filepath: str) -> pd.DataFrame:
    """
    Lê planilha CR MAXIFROTA 2026 (BASE DE DADOS pré-preenchida).

    O CR Maxifrota contém dados reais dos títulos que foram validados
    (existem tanto no Matera quanto nos Títulos em Aberto).
    Sua estrutura de colunas define o layout final do resultado.

    Args:
        filepath: Caminho do arquivo XLSX CR Maxifrota

    Returns:
        DataFrame com dados do CR + coluna doc_normalized
    """
    df = pd.read_excel(filepath)
    df = df.dropna(axis=1, how='all')
    df['doc_normalized'] = df['NUM DOC'].apply(normalize_doc)
    return df


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


def _safe_value(series: pd.Series, idx: int) -> Any:
    """
    Obtém valor seguro de uma Series, retornando None para NaN/NaT.
    """
    try:
        val = series.iloc[idx] if hasattr(series, 'iloc') else series[idx]
        if pd.isna(val):
            return None
        return val
    except (IndexError, KeyError):
        return None


def _get_column_value(
    df: pd.DataFrame,
    col_name: str,
    idx: int,
) -> Any:
    """
    Obtém valor de uma coluna específica do DataFrame pelo índice.
    Retorna None se a coluna não existir.
    """
    if col_name in df.columns:
        return _safe_value(df[col_name], idx)
    return None


def _fill_from_matera(
    matera: pd.DataFrame,
    result_columns: List[str],
    indices: List[int],
) -> pd.DataFrame:
    """
    Preenche resultado com dados do Matera para títulos que
    NÃO possuem correspondência no CR Maxifrota.

    Args:
        matera: DataFrame do Matera original
        result_columns: Lista de colunas do layout final (do CR)
        indices: Índices das linhas do Matera a incluir

    Returns:
        DataFrame preenchido com dados do Matera no layout do CR
    """
    rows = []
    for idx in indices:
        row = {}
        for col in result_columns:
            if col in COLUMN_MAPPING:
                matera_src = COLUMN_MAPPING[col][0] if len(COLUMN_MAPPING[col]) > 0 else None
                if matera_src:
                    val = _get_column_value(matera, matera_src, idx)
                    row[col] = val if val is not None else ''
                else:
                    row[col] = ''
            else:
                row[col] = ''
        row['AUXILIAR'] = 'Apenas Matera - Sem correspondência nos Títulos em Aberto'
        rows.append(row)

    result = pd.DataFrame(rows, columns=result_columns + ['AUXILIAR'])
    return result


def _build_result(
    matera: pd.DataFrame,
    complementar: pd.DataFrame,
    cr_maxifrota: pd.DataFrame,
    cr_columns: List[str],
) -> pd.DataFrame:
    """
    Constrói o DataFrame final aplicando as regras de negócio:

    1. Títulos que existem no Matera E nos Títulos em Aberto:
       → Preenchidos com dados do CR Maxifrota 2026

    2. Títulos que existem APENAS no Matera:
       → Preenchidos com dados do Matera (layout do CR)

    3. Títulos que existem APENAS nos Títulos em Aberto:
       → EXCLUÍDOS (não aparecem no resultado)
    """
    # Merge Matera × Títulos em Aberto (left join) para identificar matches
    merged = matera.merge(
        complementar,
        on='doc_normalized',
        how='left',
        suffixes=('_M', '_C')
    )

    # Determinar quais docs do Matera têm correspondência nos Títulos em Aberto
    # Se NUM DOC MATERA_C (ou NUM DOC MATERA do complementar) não for nulo, existe match
    has_match_complementar = pd.Series(False, index=merged.index)
    for candidate in ['NUM DOC MATERA_C', 'NUM DOC MATERA']:
        if candidate in merged.columns:
            col_vals = merged[candidate]
            has_match_complementar = has_match_complementar | (
                col_vals.notna() & (col_vals.astype(str).str.strip() != '') & (col_vals.astype(str).str.strip() != 'nan')
            )

    # Separar índices do Matera em dois grupos
    indices_com_match = merged.index[has_match_complementar].tolist()
    indices_sem_match = merged.index[~has_match_complementar].tolist()

    # Obter docs normalizados para busca no CR
    docs_com_match = merged.loc[indices_com_match, 'doc_normalized'].tolist()

    # Buscar correspondência no CR Maxifrota
    cr_lookup = cr_maxifrota.set_index('doc_normalized')

    result_parts = []

    # Grupo 1: Títulos com match nos Títulos em Aberto → preencher do CR
    for doc in docs_com_match:
        if doc in cr_lookup.index:
            cr_row = cr_lookup.loc[doc]
            # Se for DataFrame (docs duplicados), pega a primeira linha
            if isinstance(cr_row, pd.DataFrame):
                cr_row = cr_row.iloc[0]

            row = {}
            for col in cr_columns:
                if col in cr_row.index:
                    val = cr_row[col]
                    row[col] = val if not pd.isna(val) else ''
                else:
                    row[col] = ''
            row['AUXILIAR'] = 'OK - Validado (CR Maxifrota)'
            result_parts.append(row)
        else:
            # Título existe nas duas fontes mas NÃO está no CR → preencher do Matera
            matera_idx = merged.loc[
                merged['doc_normalized'] == doc, 'sNumDocumento_M'
            ].index
            if len(matera_idx) > 0:
                # Buscar no Matera original
                matera_doc = doc
                matera_match = matera[matera['doc_normalized'] == matera_doc]
                if len(matera_match) > 0:
                    idx = matera_match.index[0]
                    row = {}
                    for col in cr_columns:
                        if col in COLUMN_MAPPING:
                            matera_src = COLUMN_MAPPING[col][0] if len(COLUMN_MAPPING[col]) > 0 else None
                            if matera_src:
                                val = _get_column_value(matera, matera_src, idx)
                                row[col] = val if val is not None else ''
                            else:
                                row[col] = ''
                        else:
                            row[col] = ''
                    row['AUXILIAR'] = 'REVISAR - Nos Títulos em Aberto mas NÃO no CR Maxifrota'
                    result_parts.append(row)

    # Grupo 2: Títulos só no Matera → preencher do Matera
    df_matera_only = _fill_from_matera(matera, cr_columns, indices_sem_match)
    if len(df_matera_only) > 0:
        result_parts.append(df_matera_only)

    # Consolidar resultado
    if len(result_parts) > 0:
        result = pd.concat(result_parts, ignore_index=True)
    else:
        result = pd.DataFrame(columns=cr_columns + ['AUXILIAR'])

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
        DataFrame consolidado no layout do CR + coluna AUXILIAR
    """
    matera = read_matera(matera_path)
    complementar = read_complementar(complementar_path)
    cr_maxifrota = read_cr_maxifrota(cr_maxifrota_path)

    # Colunas do layout final = colunas do CR Maxifrota (exceto doc_normalized)
    cr_columns = [c for c in cr_maxifrota.columns if c != 'doc_normalized']

    result = _build_result(matera, complementar, cr_maxifrota, cr_columns)

    return result


def process_from_bytes(
    matera_bytes: bytes,
    complementar_bytes: bytes,
    cr_maxifrota_bytes: bytes
) -> pd.DataFrame:
    """
    Executa integração a partir de bytes (para Streamlit).

    Args:
        matera_bytes: Conteúdo arquivo Matera em bytes
        complementar_bytes: Conteúdo arquivo Títulos em Aberto em bytes
        cr_maxifrota_bytes: Conteúdo arquivo CR MAXIFROTA 2026 em bytes

    Returns:
        DataFrame consolidado no layout do CR + coluna AUXILIAR
    """
    # 1. Ler Matera
    matera = pd.read_csv(io.BytesIO(matera_bytes), sep=';', encoding='iso-8859-1')
    matera = matera.dropna(axis=1, how='all')
    matera['doc_normalized'] = matera['sNumDocumento'].apply(normalize_doc)

    # 2. Ler Títulos em Aberto
    complementar = pd.read_csv(io.BytesIO(complementar_bytes), sep=';', encoding='iso-8859-1')
    complementar.columns = complementar.columns.str.strip()
    complementar = complementar.dropna(axis=1, how='all')
    complementar['doc_normalized'] = complementar['NUM DOC MATERA'].apply(normalize_doc)

    # 3. Ler CR Maxifrota (com dados)
    cr_maxifrota = pd.read_excel(io.BytesIO(cr_maxifrota_bytes))
    cr_maxifrota = cr_maxifrota.dropna(axis=1, how='all')
    cr_maxifrota['doc_normalized'] = cr_maxifrota['NUM DOC'].apply(normalize_doc)

    # Colunas do layout final
    cr_columns = [c for c in cr_maxifrota.columns if c != 'doc_normalized']

    # 4. Construir resultado com regras de negócio
    result = _build_result(matera, complementar, cr_maxifrota, cr_columns)

    return result


def export_to_excel(df: pd.DataFrame, output_path: str) -> None:
    """
    Exporta DataFrame para arquivo Excel.

    Args:
        df: DataFrame a exportar
        output_path: Caminho do arquivo de saída
    """
    df.to_excel(output_path, index=False, sheet_name='Consolidado')


def export_to_bytes(df: pd.DataFrame) -> bytes:
    """
    Exporta DataFrame para bytes (Excel em memória).

    Args:
        df: DataFrame a exportar

    Returns:
        Bytes do arquivo Excel
    """
    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name='Consolidado', engine='openpyxl')
    output.seek(0)
    return output.getvalue()