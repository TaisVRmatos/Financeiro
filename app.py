"""
Integrador Financeiro — Portal RENDER
Ferramenta corporativa de conciliação de títulos financeiros.

Compatível com:
  - Python 3.11+
  - Streamlit 1.42+
  - Deploy no Render.com (porta dinâmica via $PORT)
"""

from __future__ import annotations

import os
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from processor import process_from_bytes, export_to_bytes, sanitize_for_display

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DE PÁGINA (deve ser a primeira chamada Streamlit)
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Integrador Financeiro",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": (
            "### Integrador Financeiro v2.0\n"
            "Ferramenta de conciliação de títulos financeiros.\n\n"
            "Compatível com Matera, Títulos em Aberto e CR Maxifrota."
        ),
    },
)

# ═══════════════════════════════════════════════════════════════════════
# CSS CORPORATIVO
# ═══════════════════════════════════════════════════════════════════════
_CORPORATE_CSS = """
<style>
    /* ── Fundo e tipografia ── */
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #e8edf3 100%);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1b2d 0%, #1a3350 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stDownloadButton button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] .stDownloadButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37,99,235,0.4);
    }

    /* ── Cabeçalho principal ── */
    .main-header {
        background: linear-gradient(135deg, #1a3a5c 0%, #0f2440 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        color: #ffffff;
        box-shadow: 0 4px 24px rgba(15,36,64,0.15);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .main-header .subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0.4rem;
        font-weight: 400;
    }

    /* ── Cards métricos ── */
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s ease;
    }
    .metric-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }
    .metric-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-value.ok { color: #16a34a; }
    .metric-value.warn { color: #d97706; }
    .metric-value.info { color: #2563eb; }

    /* ── Alertas / status ── */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .status-badge.success {
        background: #dcfce7;
        color: #166534;
    }
    .status-badge.warning {
        background: #fef3c7;
        color: #92400e;
    }
    .status-badge.error {
        background: #fee2e2;
        color: #991b1b;
    }

    /* ── Tabela ── */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    }
    [data-testid="stDataFrame"] th {
        background: #f1f5f9 !important;
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.03em !important;
        border-bottom: 2px solid #e2e8f0 !important;
    }

    /* ── Rodapé ── */
    .app-footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.78rem;
        padding: 2rem 1rem 1rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 2rem;
    }

    /* ── Botões ── */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }

    /* ── Ajuste mobile ── */
    @media (max-width: 768px) {
        .main-header { padding: 1.25rem; }
        .main-header h1 { font-size: 1.5rem; }
        .metric-value { font-size: 1.5rem; }
    }
</style>
"""

st.markdown(_CORPORATE_CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════
_SESSION_KEYS = {
    "result": "result_df",
    "debug_info": "debug_info",
    "file_names": "file_names",
}

_ACCEPTED_EXTENSIONS = {
    "Matera": ["csv"],
    "Títulos em Aberto": ["csv"],
    "CR Maxifrota": ["xlsx"],
}

_LABELS = {
    "Matera": "📄 Matera (CSV)",
    "Títulos em Aberto": "📋 Títulos em Aberto (CSV)",
    "CR Maxifrota": "📊 CR Maxifrota 2026 (XLSX)",
}

_HELP_TEXTS = {
    "Matera": "Arquivo CSV exportado do sistema Matera. Deve conter a coluna 'sNumDocumento'.",
    "Títulos em Aberto": "Arquivo CSV com títulos em aberto. Deve conter a coluna 'NUM DOC MATERA'.",
    "CR Maxifrota": "Planilha Excel (.xlsx) do CR Maxifrota 2026. Deve conter a coluna 'NUM DOC'.",
}

VERSION = "2.0.0"
CURRENT_YEAR = datetime.now().year


# ═══════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES DE SESSÃO
# ═══════════════════════════════════════════════════════════════════════
def _init_session() -> None:
    """Inicializa chaves da sessão se ausentes."""
    for key in _SESSION_KEYS.values():
        if key not in st.session_state:
            st.session_state[key] = None


def _clear_results() -> None:
    """Remove resultados anteriores da sessão."""
    for key in _SESSION_KEYS.values():
        st.session_state[key] = None


def _files_ready() -> bool:
    """Verifica se todos os 3 arquivos foram carregados."""
    return all(
        st.session_state.get(k) is not None
        for k in ["upload_matera", "upload_complementar", "upload_cr"]
    )


# ═══════════════════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════
def render_sidebar() -> None:
    """Renderiza a barra lateral com instruções e opções."""
    with st.sidebar:
        # Logo / título
        st.markdown(
            '<div style="text-align:center;padding:1rem 0 0.5rem;">'
            '<span style="font-size:2.5rem;">🏦</span>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<h2 style="text-align:center;margin-top:0;">Integrador<br>Financeiro</h2>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="text-align:center;color:#94a3b8;font-size:0.8rem;">v{VERSION}</p>',
            unsafe_allow_html=True,
        )

        st.divider()

        # Resumo do processo
        st.markdown("### 📋 Fluxo de Trabalho")
        st.markdown(
            """
            <ol style="color:#cbd5e1;font-size:0.85rem;line-height:1.8;">
                <li>Faça upload dos <b>3 arquivos</b></li>
                <li>Clique em <b>Processar Integração</b></li>
                <li>Visualize os resultados</li>
                <li>Exporte para <b>Excel</b></li>
            </ol>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # Upload section na sidebar (SEM form para evitar bug de reset)
        st.markdown("### 📤 Upload de Arquivos")
        matera_file = st.file_uploader(
            _LABELS["Matera"],
            type=_ACCEPTED_EXTENSIONS["Matera"],
            key="upload_matera",
            help=_HELP_TEXTS["Matera"],
        )
        complementar_file = st.file_uploader(
            _LABELS["Títulos em Aberto"],
            type=_ACCEPTED_EXTENSIONS["Títulos em Aberto"],
            key="upload_complementar",
            help=_HELP_TEXTS["Títulos em Aberto"],
        )
        cr_file = st.file_uploader(
            _LABELS["CR Maxifrota"],
            type=_ACCEPTED_EXTENSIONS["CR Maxifrota"],
            key="upload_cr",
            help=_HELP_TEXTS["CR Maxifrota"],
        )

        # Botão de processar
        st.markdown('<div style="margin-top:0.5rem;"></div>', unsafe_allow_html=True)
        process_btn = st.button(
            "⚡ Processar Integração",
            use_container_width=True,
            type="primary",
            key="btn_processar",
            disabled=not _files_ready(),
        )

        st.divider()

        # Status do processamento
        st.markdown("### 📌 Status")
        if st.session_state[_SESSION_KEYS["result"]] is not None:
            st.markdown(
                '<span class="status-badge success">✅ Processado</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="status-badge warning">⏳ Aguardando</span>',
                unsafe_allow_html=True,
            )

        st.divider()

        # Botão para limpar
        if st.button("🗑️ Limpar Resultados", use_container_width=True):
            _clear_results()
            st.rerun()

        # Rodapé da sidebar
        st.markdown(
            f'<p style="text-align:center;color:#64748b;font-size:0.7rem;margin-top:2rem;">'
            f"© {CURRENT_YEAR} Integrador Financeiro<br>Todos os direitos reservados</p>",
            unsafe_allow_html=True,
        )

    return matera_file, complementar_file, cr_file, process_btn


def render_header() -> None:
    """Renderiza cabeçalho principal da página."""
    st.markdown(
        """
        <div class="main-header">
            <h1>🏦 Integrador Financeiro</h1>
            <p class="subtitle">
                Conciliação inteligente de títulos — Matera, Títulos em Aberto & CR Maxifrota 2026
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(df: pd.DataFrame) -> None:
    """Renderiza cards métricos baseados no resultado."""
    cols = st.columns(4)

    total_titulos = len(df)

    aux_values = df["AUXILIAR"].fillna("")
    validados = int((aux_values.str.startswith("OK")).sum())
    revisar = int((aux_values.str.contains("REVISAR", na=False)).sum())
    apenas_matera = int((aux_values.str.contains("Apenas Matera", na=False)).sum())

    with cols[0]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">📊 Total de Títulos</div>
                <div class="metric-value info">{total_titulos:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[1]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">✅ Validados (CR)</div>
                <div class="metric-value ok">{validados:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[2]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">⚠️ Revisar</div>
                <div class="metric-value warn">{revisar:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[3]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">📄 Apenas Matera</div>
                <div class="metric-value">{apenas_matera:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_results_table(df: pd.DataFrame) -> None:
    """Renderiza tabela de resultados com formatação."""
    date_cols = [
        c for c in df.columns
        if "DT" in c.upper() or "DATA" in c.upper() or "EMISSAO" in c.upper() or "VENCIMENTO" in c.upper()
    ]

    money_cols = [
        c for c in df.columns
        if "VLR" in c.upper() or "VALOR" in c.upper() or "LIQUIDO" in c.upper()
    ]

    display_cols = [c for c in df.columns if c != "AUXILIAR"] + ["AUXILIAR"]
    display_df = df[display_cols].copy()

    col_config = {}
    for col in display_cols:
        if col == "AUXILIAR":
            col_config[col] = st.column_config.TextColumn(
                "🔍 Status",
                help="Indica o status de validação do título",
                width="medium",
            )
        elif col in date_cols:
            col_config[col] = st.column_config.DateColumn(col, format="DD/MM/YYYY")
        elif col in money_cols:
            col_config[col] = st.column_config.NumberColumn(col, format="R$ %.2f")
        elif "DOC" in col.upper() or "NF" in col.upper():
            col_config[col] = st.column_config.TextColumn(col, width="small")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=col_config if col_config else None,
        height=500,
    )


def render_debug_section(debug_info: dict) -> None:
    """Renderiza informações de debug com expanders."""
    with st.expander("🔧 Informações de Diagnóstico", expanded=False):
        st.caption("Detalhes técnicos do processamento para troubleshooting.")

        tab1, tab2 = st.tabs(["📋 Dados", "🖥️ Ambiente"])

        with tab1:
            if debug_info:
                for key, value in debug_info.items():
                    if isinstance(value, int):
                        st.metric(label=key, value=f"{value:,}")
                    elif isinstance(value, list):
                        st.text(f"{key}: {', '.join(value[:15])}")
                    else:
                        st.text(f"{key}: {value}")
            else:
                st.info("Nenhuma informação de diagnóstico disponível.")

        with tab2:
            st.json(
                {
                    "python_version": os.sys.version,
                    "streamlit_version": st.__version__,
                    "pandas_version": pd.__version__,
                    "port": os.environ.get("PORT", "8501 (default)"),
                    "render": os.environ.get("RENDER", "false"),
                }
            )


def render_export_section(df: pd.DataFrame) -> None:
    """Renderiza botão de exportação com preview."""
    st.markdown("### 💾 Exportar Resultado")

    col1, col2 = st.columns([2, 1])

    with col1:
        excel_bytes = export_to_bytes(df)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Integracao_Financeira_{timestamp}.xlsx"

        st.download_button(
            label=f"📥 Baixar Excel ({filename})",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col2:
        st.metric("Registros", f"{len(df):,}")
        st.metric("Colunas", f"{len(df.columns):,}")


def render_empty_state() -> None:
    """Renderiza estado inicial quando não há dados."""
    st.markdown(
        """
        <div style="text-align:center;padding:4rem 2rem;">
            <div style="font-size:4rem;margin-bottom:1rem;">📂</div>
            <h3 style="color:#64748b;margin-bottom:0.5rem;">Nenhum arquivo processado</h3>
            <p style="color:#94a3b8;font-size:0.95rem;">
                Utilize o painel lateral para fazer upload dos arquivos<br>
                e clique em <b>Processar Integração</b> para iniciar.
            </p>
            <div style="margin-top:2rem;padding:1.5rem;background:#f8fafc;border-radius:12px;display:inline-block;text-align:left;">
                <p style="color:#475569;font-size:0.85rem;margin:0;">
                    📄 <b>Matera</b> — CSV com coluna <code>sNumDocumento</code><br>
                    📋 <b>Títulos em Aberto</b> — CSV com coluna <code>NUM DOC MATERA</code><br>
                    📊 <b>CR Maxifrota</b> — Excel com coluna <code>NUM DOC</code>
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Renderiza rodapé da aplicação."""
    st.markdown(
        f"""
        <div class="app-footer">
            <p>🏦 Integrador Financeiro v{VERSION} &copy; {CURRENT_YEAR}</p>
            <p style="font-size:0.72rem;color:#cbd5e1;">
                Deploy via Render.com | Python {os.sys.version_info.major}.{os.sys.version_info.minor}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# LÓGICA DE PROCESSAMENTO
# ═══════════════════════════════════════════════════════════════════════
def process_files(
    matera_bytes: bytes,
    complementar_bytes: bytes,
    cr_bytes: bytes,
) -> tuple[Optional[pd.DataFrame], Optional[str], dict]:
    """
    Executa o pipeline de integração com tratamento completo de erros.

    Returns:
        Tuple de (DataFrame ou None, mensagem de erro ou None, debug_info)
    """
    debug_info = {
        "matera_size_kb": round(len(matera_bytes) / 1024, 1),
        "complementar_size_kb": round(len(complementar_bytes) / 1024, 1),
        "cr_size_kb": round(len(cr_bytes) / 1024, 1),
    }

    try:
        result = process_from_bytes(matera_bytes, complementar_bytes, cr_bytes)
        debug_info["raw_rows"] = len(result)

        result = sanitize_for_display(result)
        debug_info["display_rows"] = len(result)
        debug_info["columns"] = list(result.columns[:20])

        if "AUXILIAR" in result.columns:
            aux = result["AUXILIAR"].fillna("")
            debug_info["validados_ok"] = int(
                (aux.str.startswith("OK")).sum()
            )
            debug_info["revisar"] = int(
                (aux.str.contains("REVISAR", na=False)).sum()
            )
            debug_info["apenas_matera"] = int(
                (aux.str.contains("Apenas Matera", na=False)).sum()
            )

        return result, None, debug_info

    except ValueError as e:
        return None, str(e), debug_info
    except Exception as e:
        tb = traceback.format_exc()
        error_msg = f"❌ **Erro inesperado durante processamento:**\n\n```\n{tb[-1500:]}\n```"
        debug_info["error_traceback"] = tb[-2000:]
        return None, error_msg, debug_info


# ═══════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════
def main() -> None:
    """Função principal da aplicação Streamlit."""
    _init_session()

    render_header()

    # Sidebar com uploads
    matera_file, complementar_file, cr_file, process_btn = render_sidebar()

    # Container principal
    result_container = st.container()

    with result_container:
        if process_btn:
            # Validação de uploads
            missing = []
            if matera_file is None:
                missing.append("Matera (CSV)")
            if complementar_file is None:
                missing.append("Títulos em Aberto (CSV)")
            if cr_file is None:
                missing.append("CR Maxifrota 2026 (XLSX)")

            if missing:
                st.error(
                    f"⚠️ **Arquivos obrigatórios não enviados:** {', '.join(missing)}"
                )
                st.info("Por favor, faça upload de todos os 3 arquivos antes de processar.")
            else:
                with st.status(
                    "🔄 Processando integração financeira...", expanded=True
                ) as status:
                    st.write("📖 Lendo arquivos...")
                    matera_bytes = matera_file.getvalue()
                    complementar_bytes = complementar_file.getvalue()
                    cr_bytes = cr_file.getvalue()

                    st.write("🔍 Normalizando documentos...")
                    result, error, debug_info = process_files(
                        matera_bytes, complementar_bytes, cr_bytes
                    )

                    if error:
                        status.update(
                            label="❌ Falha no processamento",
                            state="error",
                            expanded=True,
                        )
                        st.error(error)
                        st.session_state[_SESSION_KEYS["result"]] = None
                        st.session_state[_SESSION_KEYS["debug_info"]] = debug_info
                    else:
                        status.update(
                            label="✅ Processamento concluído com sucesso!",
                            state="complete",
                            expanded=False,
                        )
                        st.session_state[_SESSION_KEYS["result"]] = result
                        st.session_state[_SESSION_KEYS["debug_info"]] = debug_info
                        st.session_state[_SESSION_KEYS["file_names"]] = {
                            "matera": matera_file.name,
                            "complementar": complementar_file.name,
                            "cr": cr_file.name,
                        }

        # Exibição de resultados
        result_df = st.session_state[_SESSION_KEYS["result"]]
        debug_info = st.session_state[_SESSION_KEYS["debug_info"]]

        if result_df is not None and len(result_df) > 0:
            st.markdown("---")
            st.markdown("## 📊 Resultados da Integração")
            render_metrics(result_df)
            st.markdown("---")
            st.markdown("### 📋 Títulos Processados")
            render_results_table(result_df)
            st.markdown("---")
            render_export_section(result_df)
            if debug_info:
                render_debug_section(debug_info)

        elif result_df is not None and len(result_df) == 0:
            st.warning(
                "⚠️ O processamento foi concluído, mas **nenhum título** foi encontrado. "
                "Verifique se os arquivos enviados estão corretos."
            )
            if debug_info:
                render_debug_section(debug_info)

        elif debug_info:
            render_debug_section(debug_info)

        else:
            render_empty_state()

    render_footer()


if __name__ == "__main__":
    main()