import streamlit as st
import pandas as pd
import numpy as np
from processor import process_from_bytes, export_to_bytes, sanitize_for_display
import io

# ---------------------------------------------------------------------------
# Compatibilidade com pandas 3.x (usa PyArrow backend por padrão no pandas 3)
# Desabilita TODAS as opções future que ativam ArrowDtype
# ---------------------------------------------------------------------------
_pandas_major = int(pd.__version__.split('.')[0])
if _pandas_major >= 3:
    # Desabilita infer_string (causa ArrowDtype nas strings)
    try:
        pd.options.future.infer_string = False
    except Exception:
        pass
    # Desabilita silent downcasting
    try:
        pd.options.future.no_silent_downcasting = False
    except Exception:
        pass
    # Para qualquer outra opção future que possa causar Arrow
    for opt in ['infer_string', 'no_silent_downcasting', 'use_arrow_dtype']:
        try:
            if hasattr(pd.options.future, opt):
                setattr(pd.options.future, opt, False)
        except Exception:
            pass


def main():
    """
    Aplicação Streamlit para integração de planilhas financeiras.
    """
    st.set_page_config(
        page_title="Integrador de Planilhas Financeiras",
        page_icon="📊",
        layout="wide"
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
            type=['csv'],
            key='matera',
            help="Arquivo CSV com separador ;"
        )
    
    with col2:
        st.markdown("**Complementar**")
        complementar_file = st.file_uploader(
            "Título em Aberto.csv",
            type=['csv'],
            key='complementar',
            help="Arquivo CSV com separador ;"
        )
    
    with col3:
        st.markdown("**Template**")
        template_file = st.file_uploader(
            "CR MAXIFROTA 2026.xlsx",
            type=['xlsx'],
            key='template',
            help="Arquivo Excel com layout obrigatório"
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
                            matera_bytes,
                            complementar_bytes,
                            template_bytes
                        )
                        
                        # Armazenar em session_state
                        st.session_state.result_df = result_df
                        
                        st.success(
                            f"✅ Consolidação concluída! "
                            f"{len(result_df)} registros processados."
                        )
                
                except ValueError as e:
                    # Erros de validação com mensagens detalhadas do processor
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
        if 'result_df' in st.session_state:
            st.divider()
            
            st.subheader("📋 Prévia dos Dados")
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Registros", len(st.session_state.result_df))
            with col2:
                revisar_count = (
                    st.session_state.result_df.astype(str).eq('REVISAR').sum().sum()
                )
                st.metric("Campos para Revisar", revisar_count)
            with col3:
                st.metric("Colunas", len(st.session_state.result_df.columns))
            with col4:
                st.metric("Memória", 
                    f"{st.session_state.result_df.memory_usage(deep=True).sum() / 1024:.1f} KB"
                )
            
            # Visualizar dados
            st.markdown("**Primeiras 10 linhas:**")
            st.dataframe(
                sanitize_for_display(st.session_state.result_df.head(10)),
                use_container_width=True,
                height=400
            )
            
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
                    use_container_width=True
                )
            
            with col2:
                csv_bytes = st.session_state.result_df.to_csv(
                    index=False,
                    sep=';',
                    encoding='utf-8'
                ).encode('utf-8')
                st.download_button(
                    label="📄 Baixar CSV",
                    data=csv_bytes,
                    file_name="consolidado_financeiro.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col3:
                # Dados detalhados para debugging
                if st.checkbox("Mostrar dados detalhados (debug)"):
                    st.dataframe(
                        sanitize_for_display(st.session_state.result_df),
                        use_container_width=True
                    )
    
    else:
        st.info("⏳ Carregue os 3 arquivos para iniciar o processamento.")


if __name__ == "__main__":
    main()
