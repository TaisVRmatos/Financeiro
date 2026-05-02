import streamlit as st
import pandas as pd
import numpy as np

from processor import process_from_bytes, export_to_bytes, sanitize_for_display


def _safe_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara DataFrame para exibição Streamlit, com fallback completo.
    Garante que não haja ArrowDtype ou tipos não-suportados.
    """
    df = sanitize_for_display(df)
    try:
        return df.astype(str)
    except Exception:
        data = {}
        for col in df.columns:
            try:
                data[col] = [str(v) if v is not None else "" for v in df[col].tolist()]
            except Exception:
                data[col] = [""] * len(df)
        return pd.DataFrame(data, columns=list(data.keys()))


def _safe_memory_usage(df: pd.DataFrame) -> str:
    """Calcula uso de memória com segurança."""
    try:
        mem = df.memory_usage(deep=False).sum() / 1024
        return f"{mem:.1f} KB"
    except Exception:
        return "N/D"


def _safe_revisar_count(df: pd.DataFrame) -> int:
    """Conta campos 'REVISAR' com segurança."""
    try:
        safe = _safe_dataframe_for_display(df)
        return int((safe == "REVISAR").sum().sum())
    except Exception:
        return 0


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

        # Botão sem colunas aninhadas (evita erro removeChild do React)
        if st.button("🔄 Consolidar Dados", use_container_width=True):
            try:
                with st.spinner("Processando arquivos..."):
                    matera_bytes = matera_file.read()
                    complementar_bytes = complementar_file.read()
                    template_bytes = template_file.read()

                    result_df = process_from_bytes(
                        matera_bytes, complementar_bytes, template_bytes
                    )

                    # Sanitizar ANTES de armazenar no session_state
                    result_df = sanitize_for_display(result_df)

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

            # Visualizar dados (st.table = renderização estática HTML, sem React)
            st.markdown("**Primeiras 10 linhas:**")
            try:
                display_df = _safe_dataframe_for_display(
                    st.session_state.result_df.head(10)
                )
                st.table(display_df)
            except Exception:
                st.info("ℹ️ Prévia não disponível neste momento. "
                        "Faça download do arquivo para visualizar os dados.")

            # Download
            st.divider()
            st.subheader("📥 Download")

            col1, col2 = st.columns(2)

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

    else:
        st.info("⏳ Carregue os 3 arquivos para iniciar o processamento.")


if __name__ == "__main__":
    main()