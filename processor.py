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
    Lê arquivo complementar (segunda fonte).
    
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


def read_template(filepath: str) -> pd.DataFrame:
    """
    Lê template Excel final para obter layout obrigatório.
    
    Args:
        filepath: Caminho do arquivo XLSX template
    
    Returns:
        DataFrame vazio com colunas do template
    """
    df = pd.read_excel(filepath)
    return df.iloc[0:0].copy()


# ---------------------------------------------------------------------------
# MAPEAMENTO: coluna do template  ->  [fonte Matera, fonte Complementar]
# A ordem define prioridade: tenta Matera primeiro, depois Complementar.
# Coluna vazia (= []) significa que não há mapeamento automático (REVISAR).
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
    'SCORE CLASS':             [],                                     # sem mapeamento
    'PROB DEFAULT (%)':        [],                                     # sem mapeamento
    'TENDÊNCIA':               [],                                     # sem mapeamento
    'PREVISAO DE PAGAMENTO':   [],                                     # sem mapeamento
    'BANCO':                   ['sBanco',                 'BANCO'],
    'DATA BLOQUEIO':           ['DATA BLOQUEIO',          'DATA BLOQUEIO'],
    'CODIGO PAGAMENTO':        [],                                     # sem mapeamento
    'ATRASO':                  ['ATRASO',                 'ATRASO'],
    'LINK NFSE':               ['LINK NFSE',              'LINK NFSE'],
    'SISTEMA':                 ['SISTEMA',                'SISTEMA'],
    'RBASE RAIZ':              ['RBASE RAIZ',             'RBASE RAIZ'],
}


def _find_column_value(
    merged: pd.DataFrame,
    matera_col: Optional[str],
    compl_col: Optional[str],
) -> pd.Series:
    """
    Busca valor de uma coluna no DataFrame merged, respeitando prioridade
    Matera > Complementar > REVISAR, e tratando os sufixos _M / _C
    gerados pelo merge.

    O DataFrame merged possui colunas renomeadas pelo pandas quando há
    nomes duplicados entre as duas fontes. Exemplo:
        - 'EXECUTIVO'  ->  'EXECUTIVO_M' (Matera)  e  'EXECUTIVO_C' (Complementar)
        - Colunas exclusivas de uma fonte mantêm o nome original.

    Estratégia de busca (por ordem de prioridade):
      1. nome_M   (coluna vinda do Matera)
      2. nome     (coluna sem sufixo – exclusiva do Matera ou sem conflito)
      3. nome_C   (coluna vinda do Complementar)
    """

    candidates: List[str] = []

    # Prioridade 1: Matera com sufixo _M
    if matera_col:
        candidates.append(f"{matera_col}_M")
        # Prioridade 2: nome original (pode ser exclusivo do Matera)
        candidates.append(matera_col)

    # Prioridade 3: Complementar com sufixo _C
    if compl_col:
        candidates.append(f"{compl_col}_C")
        # Prioridade 4: nome original do complementar (se diferente do Matera)
        if compl_col != matera_col:
            candidates.append(compl_col)

    for candidate in candidates:
        if candidate in merged.columns:
            series = merged[candidate].copy()
            # Converte para string e substitui NaN / NaT por None (depois REVISAR)
            result = series.astype(str)
            result = result.replace('nan', None)
            result = result.replace('NaT', None)
            result = result.replace('<NA>', None)
            result = result.fillna('REVISAR')
            result = result.replace('None', 'REVISAR')
            return result

    # Fallback: nenhuma coluna encontrada
    return pd.Series(['REVISAR'] * len(merged), index=merged.index)


def fill_template(merged: pd.DataFrame, template: pd.DataFrame) -> pd.DataFrame:
    """
    Preenche template com dados consolidados respeitando regra de negócio:
    - Prioridade: Matera > Complementar > "REVISAR"
    - Adiciona coluna AUXILIAR sinalizando registros sem match no complementar
    
    Args:
        merged: DataFrame consolidado (resultado do merge)
        template: DataFrame com estrutura do template
    
    Returns:
        DataFrame preenchido com layout obrigatório + coluna AUXILIAR
    """
    result = pd.DataFrame(columns=template.columns)

    # Preenche cada coluna do template usando o mapeamento
    for col_template in template.columns:
        if col_template in COLUMN_MAPPING:
            sources = COLUMN_MAPPING[col_template]
            matera_src = sources[0] if len(sources) > 0 else None
            compl_src = sources[1] if len(sources) > 1 else None
        else:
            matera_src = None
            compl_src = None

        result[col_template] = _find_column_value(merged, matera_src, compl_src)

    # Coluna AUXILIAR: sinaliza registros sem correspondência no complementar
    # Detecta se a coluna de documento do complementar veio vazia (NaN = sem match)
    aux_values = []
    for idx in merged.index:
        row = merged.loc[idx]

        # Tenta achar o campo 'NUM DOC MATERA' no merged (pode ter sufixo _C)
        doc_compl = None
        for candidate in ['NUM DOC MATERA_C', 'NUM DOC MATERA']:
            if candidate in merged.columns:
                val = row[candidate]
                if not pd.isna(val) and str(val).strip() != '' and str(val).strip() != 'nan':
                    doc_compl = val
                    break

        if doc_compl is not None:
            aux_values.append('OK - Encontrado nos Títulos em Aberto')
        else:
            aux_values.append('REVISAR - Não encontrado no complementar')

    result['AUXILIAR'] = aux_values

    return result


def merge_data(matera: pd.DataFrame, complementar: pd.DataFrame) -> pd.DataFrame:
    """
    Realiza merge entre dados Matera e complementares.
    Matera é FONTE DE VERDADE, seus valores prevalecem.
    
    Args:
        matera: DataFrame da fonte de verdade (Matera)
        complementar: DataFrame da fonte complementar
    
    Returns:
        DataFrame consolidado
    """
    merged = matera.merge(
        complementar,
        on='doc_normalized',
        how='left',
        suffixes=('_M', '_C')
    )
    return merged


def process_integration(
    matera_path: str,
    complementar_path: str,
    template_path: str
) -> pd.DataFrame:
    """
    Executa fluxo completo de integração.
    
    Args:
        matera_path: Caminho arquivo Matera
        complementar_path: Caminho arquivo complementar
        template_path: Caminho arquivo template Excel
    
    Returns:
        DataFrame consolidado com layout final + coluna AUXILIAR
    """
    matera = read_matera(matera_path)
    complementar = read_complementar(complementar_path)
    template = read_template(template_path)

    merged = merge_data(matera, complementar)
    result = fill_template(merged, template)

    return result


def process_from_bytes(
    matera_bytes: bytes,
    complementar_bytes: bytes,
    template_bytes: bytes
) -> pd.DataFrame:
    """
    Executa integração a partir de bytes (para Streamlit).
    
    Args:
        matera_bytes: Conteúdo arquivo Matera em bytes
        complementar_bytes: Conteúdo arquivo complementar em bytes
        template_bytes: Conteúdo arquivo template em bytes
    
    Returns:
        DataFrame consolidado com layout final + coluna AUXILIAR
    """
    # 1. Converter bytes para DataFrames
    matera = pd.read_csv(io.BytesIO(matera_bytes), sep=';', encoding='iso-8859-1')
    matera = matera.dropna(axis=1, how='all')
    matera['doc_normalized'] = matera['sNumDocumento'].apply(normalize_doc)

    complementar = pd.read_csv(io.BytesIO(complementar_bytes), sep=';', encoding='iso-8859-1')
    complementar.columns = complementar.columns.str.strip()
    complementar = complementar.dropna(axis=1, how='all')
    complementar['doc_normalized'] = complementar['NUM DOC MATERA'].apply(normalize_doc)

    template = pd.read_excel(io.BytesIO(template_bytes))
    template = template.iloc[0:0].copy()

    # 2. Consolidar dados
    merged = merge_data(matera, complementar)

    # 3. Preencher template (usa a mesma função que process_integration)
    result = fill_template(merged, template)

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