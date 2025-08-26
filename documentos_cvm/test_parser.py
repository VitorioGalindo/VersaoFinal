import pytest
pytest.skip(reason="manual parser test; requires external resources", allow_module_level=True)

# test_parser.py
from bs4 import BeautifulSoup
import pandas as pd
import re

# Importe a função que queremos testar
from realtime_scraper import parse_cvm_table

def get_dummy_cnpj_map():
    """Cria um mapa de CNPJ falso para o teste, incluindo um CNPJ da página de exemplo."""
    return {
        '00000000000191': 1,
        '60746948000112': 2,
    }

if __name__ == '__main__':
    print("--- Iniciando teste do parser HTML ---")
    cnpj_map = get_dummy_cnpj_map()
    try:
        with open('cvm_results_page.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("\nERRO: Arquivo 'cvm_results_page.html' não encontrado.")
        print("Por favor, salve a página de resultados da CVM antes de rodar este teste.")
        exit()
    soup = BeautifulSoup(html_content, 'lxml')
    extracted_documents = parse_cvm_table(soup, cnpj_map)
    if not extracted_documents:
        print("\nFALHA: Nenhum documento foi extraído. Verifique os seletores na função 'parse_cvm_table'.")
    else:
        print(f"\nSUCESSO: {len(extracted_documents)} documentos extraídos com sucesso!")
        print("Amostra dos dados extraídos:")
        df = pd.DataFrame(extracted_documents)
        print(df.head())
    print("\n--- Teste do parser concluído ---")
