import streamlit as st
import pandas as pd
import numpy as np

from processor import process_from_bytes, export_to_bytes, sanitize_for_display

# ---------------------------------------------------------------------------
# Compatibilidade com pandas 3.x (usa PyArrow backend por padrão no pandas 3)
# Desabilita TODAS as opções future que ativam ArrowDtype
# ---------------------------------------------------------------------------
_pandas_major = int(pd.__version__.split(".")[0])
if _pandas_major >= 3:
    for opt in ["infer_string", "no_silent_downcasting", "use_arrow_dtype"]:
        try:
            if hasattr(pd.options.future, opt):
                setattr(pd.options.future, opt, False)
        except Exception:
            pass


def _safe_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara DataFrame para exibição Streamlit, com fallback completo.
    Garante que não haja ArrowDtype ou tipos não-suportados.
    Todas as colunas viram string ou float64 nativo.
    """
    df = sanitize_for_display(df)
    # Garantia extra: converte TUDO para string (seguro universal)
    try:
        safe = df.astype(str)
        return safe
    except Exception:
        pass
    # Último recurso: constrói DataFrame novo célula por célula
    data = {}
    for col in df.columns:
        try:
            data[col] = [str(v) if v is not None else "" for v in df[col].tolist()]
        except Exception:
            data[col] = [""] * len(df)
    return pd.DataFrame(data, columns=list(data.keys()))


def _safe_memory_usage(df: pd.DataFrame) -> str:
    """Calcula uso de memória com segurança para pandas 3.x."""
    try:
        mem = df.memory_usage(deep=True).sum() / 1024
        return f"{mem:.1f} KB"
    except Exception:
        try:
            mem = df.memory_usage(deep=False).sum() / 1024
            return f"{mem:.1f} KB"
        except Exception:
            return "N/D"


def _safe_revisar_count(df: pd.DataFrame) -> int:
    """Conta campos 'REVISAR' com segurança."""
    try:
        safe = _safe_dataframe_for_display(df)
        return (safe == "REVISAR").sum().sum()
    except Exception:
        return 0


def _render_dataframe(df: pd.DataFrame, height: int = 400, full: bool = False):
    """
    Renderiza DataFrame no Streamlit com fallback em caso de erro PyArrow.
    Tenta st.dataframe() primeiro; se falhar, usa st.write().
    """
    try:
        display_df = sanitize_for_display(df.head(10) if not full else df)
        st.dataframe(display_df, use_container_width=True, height=height)
    except Exception:
        try:
            safe = _safe_dataframe_for_display(df.head(10) if not full else df)
            st.dataframe(safe, use_container_width=True, height=height)
        except Exception:
            try:
                st.write(df.head(10).to_dict(orient="records") if not full else df.to_dict(orient="records"))
            except Exception as e:
                st.error(f"❌ Erro ao renderizar dados: {e}")


def main():
    """
    Aplicação Streamlit para integração de planilhas financeiras.
    """
    st.set_page_config(
        page_title="Integrador de Planilhas Financeiras",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 Integrador de Planilhas Financeiras")
    st.markdown(
        """
        Consolidação automática de dados financeiros com validação de integridade.

        **Arquivos esperados:**
        - Titulos em aberto Matera.csv (FONTE DE VERDADE)
        - Título em Aberto.csv (Fonte Complementar)
        - CR MAXIFROTA 2026.xlsx (Base de Dados Pré-preenchida)
        """
    )

    st.divider()

    # Seção de upload
    st.subheader("📁 Carregue os Arquivos")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Matera (Fonte Verdade)**")
        matera_file = st.file_uploader(
            "Titulos em aberto Matera.csv",
            type=["csv"],
            key="matera",
            help="Arquivo CSV com separador ;",
        )

    with col2:
        st.markdown("**Complementar**")
        complementar_file = st.file_uploader(
            "Título em Aberto.csv",
            type=["csv"],
            key="complementar",
            help="Arquivo CSV com separador ;",
        )

    with col3:
        st.markdown("**Template**")
        template_file = st.file_uploader(
            "CR MAXIFROTA 2026.xlsx",
            type=["xlsx"],
            key="template",
            help="Arquivo Excel com layout obrigatório",
        )

    st.divider()

    # Seção de processamento
    if matera_file and complementar_file and template_file:
        st.subheader("⚙️ Processamento")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Consolidar Dados", use_container_width=True):
                try:
                    with st.spinner("Processando arquivos..."):
                        # Ler bytes dos arquivos
                        matera_bytes = matera_file.read()
                        complementar_bytes = complementar_file.read()
                        template_bytes = template_file.read()

                        # Processar integração
                        result_df = process_from_bytes(
                            matera_bytes, complementar_bytes, template_bytes
                        )

                        # Sanitizar ANTES de armazenar no session_state (evita erros posteriores)
                        result_df = sanitize_for_display(result_df)

                        # Armazenar em session_state
                        st.session_state.result_df = result_df

                        st.success(
                            f"✅ Consolidação concluída! "
                            f"{len(result_df)} registros processados."
                        )

                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(
                        f"❌ Erro inesperado ao processar os arquivos:\n\n"
                        f"**{type(e).__name__}:** {str(e)}\n\n"
                        f"Verifique se:\n"
                        f"- Os arquivos CSV estão no formato válido (separador ; ou ,)\n"
                        f"- O arquivo Excel está no formato .xlsx (não .xls)\n"
                        f"- As colunas obrigatórias estão presentes em cada arquivo"
                    )

        # Exibir resultados
        if "result_df" in st.session_state:
            st.divider()

            st.subheader("📋 Prévia dos Dados")

            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Registros", len(st.session_state.result_df))
            with col2:
                revisar_count = _safe_revisar_count(st.session_state.result_df)
                st.metric("Campos para Revisar", int(revisar_count))
            with col3:
                st.metric("Colunas", len(st.session_state.result_df.columns))
            with col4:
                st.metric("Memória", _safe_memory_usage(st.session_state.result_df))

            # Visualizar dados
            st.markdown("**Primeiras 10 linhas:**")
            _render_dataframe(st.session_state.result_df, height=400)

            # Download
            st.divider()
            st.subheader("📥 Download")

            col1, col2, col3 = st.columns(3)

            with col1:
                excel_bytes = export_to_bytes(st.session_state.result_df)
                st.download_button(
                    label="📊 Baixar Excel",
                    data=excel_bytes,
                    file_name="consolidado_financeiro.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

            with col2:
                csv_bytes = st.session_state.result_df.to_csv(
                    index=False, sep=";", encoding="utf-8"
                ).encode("utf-8")
                st.download_button(
                    label="📄 Baixar CSV",
                    data=csv_bytes,
                    file_name="consolidado_financeiro.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col3:
                if st.checkbox("Mostrar dados detalhados (debug)"):
                    _render_dataframe(st.session_state.result_df, full=True, height=600)

    else:
        st.info("⏳ Carregue os 3 arquivos para iniciar o processamento.")


if __name__ == "__main__":
    main()