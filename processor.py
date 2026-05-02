import pandas as pd
import numpy as np
from typing import Tuple, Optional
import io


def normalize_doc(valor: any) -> Optional[str]:
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
    
    # Remove colunas vazias
    df = df.dropna(axis=1, how='all')
    
    # Normaliza chave de documento
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
    
    # Remove espaços das colunas e linhas
    df.columns = df.columns.str.strip()
    
    # Remove colunas vazias
    df = df.dropna(axis=1, how='all')
    
    # Normaliza chave de documento
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
    return df.iloc[0:0].copy()  # Retorna apenas estrutura vazia


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
    # Merge na chave normalizada
    merged = matera.merge(
        complementar,
        on='doc_normalized',
        how='left',
        suffixes=('_M', '_C')
    )
    
    return merged


def fill_template(merged: pd.DataFrame, template: pd.DataFrame) -> pd.DataFrame:
    """
    Preenche template com dados consolidados respeitando regra de negócio:
    - Prioridade: Matera > Complementar > "REVISAR"
    
    Args:
        merged: DataFrame consolidado
        template: DataFrame com estrutura do template
    
    Returns:
        DataFrame preenchido com layout obrigatório
    """
    result = pd.DataFrame(columns=template.columns)
    
    for col in template.columns:
        result[col] = _get_column_value(merged, col)
    
    return result


def _get_column_value(merged: pd.DataFrame, col: str) -> pd.Series:
    """
    Retorna valores para coluna específica do template,
    aplicando regras de prioridade.
    
    Args:
        merged: DataFrame consolidado
        col: Nome da coluna do template
    
    Returns:
        Series com valores preenchidos
    """
    mapping = {
        'EMPRESA': ['sEmpresa'],
        'EXECUTIVO': ['EXECUTIVO'],
        'PRODUTO': ['PRODUTO'],
        'CNPJ': ['CNPJ'],
        'RBASE': ['RBASE'],
        'NF': ['NR NFEM'],
        'NUM DOC': ['sNumDocumento'],
        'CLIENTE': ['sCliente'],
        'CLIENTE 2': ['NOME CLIENTE'],
        'UF': ['UF'],
        'CIDADE': ['CIDADE'],
        'GRUPO': ['NOME CLIENTE'],
        'TIPO': ['TIPO'],
        'COND PAGTO': ['COND PAGTO'],
        'DT EMISSAO': ['dtEmissao', 'DT EMISSAO'],
        'DT VENCIMENTO': ['dtUltVcto', 'DT VENCIMENTO'],
        'VLR TITULO': ['nVlrParcela', 'VLR TITULO'],
        'VLR SALDO': ['nVlrPendParcela', 'VLR SALDO'],
        'IR': ['IR RETIDO'],
        'ISS': ['ISS RETIDO'],
        'LIQUIDO CORRETO': ['CSLL RETIDO'],
        'PAGA NA DATA': ['COFINS'],
        'RISCO DE INADIMPLÊNCIA': ['PIS'],
        'CREDIT SCORE': ['ATRASO'],
        'SCORE CLASS': [],
        'PROB DEFAULT (%)': [],
        'TENDÊNCIA': [],
        'PREVISAO DE PAGAMENTO': [],
        'BANCO': ['sBanco'],
        'DATA BLOQUEIO': ['DATA BLOQUEIO'],
        'CODIGO PAGAMENTO': [],
        'ATRASO': ['ATRASO'],
        'LINK NFSE': ['LINK NFSE'],
        'SISTEMA': ['SISTEMA'],
        'RBASE RAIZ': ['RBASE RAIZ'],
    }
    
    sources = mapping.get(col, [])
    
    for source in sources:
        if source in merged.columns:
            result = merged[source].fillna('REVISAR').astype(str)
            return result.replace('nan', 'REVISAR').replace('NaT', 'REVISAR')
    
    # Se nenhuma coluna encontrada, retorna "REVISAR"
    return pd.Series(['REVISAR'] * len(merged), index=merged.index)


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
        DataFrame consolidado com layout final
    """
    # 1. Ler arquivos
    matera = read_matera(matera_path)
    complementar = read_complementar(complementar_path)
    template = read_template(template_path)
    
    # 2. Consolidar dados
    merged = merge_data(matera, complementar)
    
    # 3. Preencher template
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
        DataFrame consolidado com layout final
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
    merged = matera.merge(
        complementar,
        on='doc_normalized',
        how='left',
        suffixes=('_M', '_C')
    )
    
    # 3. Preencher template
    result = pd.DataFrame(columns=template.columns)
    
    for col in template.columns:
        result[col] = _get_column_value(merged, col)
    
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
