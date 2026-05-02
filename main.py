#!/usr/bin/env python3
"""
Script de execução direta para consolidação de planilhas.
Uso: python main.py <matera.csv> <complementar.csv> <template.xlsx> <output.xlsx>
"""

import sys
import argparse
from pathlib import Path
from processor import process_integration, export_to_excel


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Consolidador de Planilhas Financeiras',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py matera.csv complementar.csv template.xlsx output.xlsx
  python main.py --help
        """
    )
    
    parser.add_argument(
        'matera',
        type=str,
        help='Caminho do arquivo Matera.csv'
    )
    
    parser.add_argument(
        'complementar',
        type=str,
        help='Caminho do arquivo complementar.csv'
    )
    
    parser.add_argument(
        'template',
        type=str,
        help='Caminho do arquivo template.xlsx'
    )
    
    parser.add_argument(
        'output',
        nargs='?',
        default='consolidado.xlsx',
        help='Caminho de saída (padrão: consolidado.xlsx)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Exibe detalhes do processamento'
    )
    
    args = parser.parse_args()
    
    # Validar arquivos
    matera_path = Path(args.matera)
    complementar_path = Path(args.complementar)
    template_path = Path(args.template)
    
    if args.verbose:
        print(f"🔍 Validando arquivos...")
    
    if not matera_path.exists():
        print(f"❌ Arquivo não encontrado: {args.matera}")
        sys.exit(1)
    
    if not complementar_path.exists():
        print(f"❌ Arquivo não encontrado: {args.complementar}")
        sys.exit(1)
    
    if not template_path.exists():
        print(f"❌ Arquivo não encontrado: {args.template}")
        sys.exit(1)
    
    try:
        if args.verbose:
            print(f"\n📂 Arquivos encontrados:")
            print(f"   Matera: {matera_path.absolute()}")
            print(f"   Complementar: {complementar_path.absolute()}")
            print(f"   Template: {template_path.absolute()}")
            print(f"\n🔄 Processando...")
        
        # Processar
        result = process_integration(
            str(matera_path),
            str(complementar_path),
            str(template_path)
        )
        
        if args.verbose:
            print(f"✅ Consolidação concluída")
            print(f"   Registros processados: {len(result)}")
            print(f"   Colunas: {len(result.columns)}")
            
            revisar_count = (result.astype(str) == 'REVISAR').sum().sum()
            revisar_percent = revisar_count / (len(result) * len(result.columns)) * 100
            print(f"   Campos REVISAR: {revisar_count} ({revisar_percent:.2f}%)")
            print(f"\n💾 Exportando...")
        
        # Exportar
        export_to_excel(result, args.output)
        
        print(f"✅ Sucesso! Arquivo salvo em: {args.output}")
        
        if args.verbose:
            output_path = Path(args.output)
            print(f"   Tamanho: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        return 0
    
    except Exception as e:
        print(f"❌ Erro ao processar: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
