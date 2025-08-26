import requests
from bs4 import BeautifulSoup
import os

# Testar o link do documento
download_url = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?NumeroProtocoloEntrega=1415320"

print(f"Abrindo link: {download_url}")

# Tentar com headers mais completos
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

try:
    response = requests.get(download_url, headers=headers, allow_redirects=True)
    print(f"Status: {response.status_code}")
    
    # Analisar o conteúdo HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Procurar por formulários e seus campos
    forms = soup.find_all('form')
    if forms:
        print(f"Encontrados {len(forms)} formulários na página")
        for i, form in enumerate(forms):
            print(f"\nFormulário {i+1}:")
            print(f"  Action: {form.get('action')}")
            print(f"  Method: {form.get('method')}")
            
            # Procurar campos do formulário
            inputs = form.find_all('input')
            if inputs:
                print(f"  Campos do formulário:")
                for input_field in inputs:
                    field_name = input_field.get('name', 'sem nome')
                    field_type = input_field.get('type', 'sem tipo')
                    field_value = input_field.get('value', 'sem valor')
                    print(f"    - {field_name} ({field_type}): {field_value}")
    
    # Procurar por scripts que possam conter informações
    scripts = soup.find_all('script')
    if scripts:
        print(f"\nEncontrados {len(scripts)} scripts")
        for script in scripts:
            if script.string and 'download' in script.string.lower():
                print("Script com referência a download encontrado:")
                print(script.string[:200] + "..." if len(script.string) > 200 else script.string)
                
except Exception as e:
    print(f"Erro: {e}")