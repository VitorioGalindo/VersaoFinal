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
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    # Analisar o conteúdo HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Imprimir título da página
    title = soup.find('title')
    if title:
        print(f"Título da página: {title.text}")
    
    # Procurar por formulários ou links de download
    forms = soup.find_all('form')
    if forms:
        print(f"Encontrados {len(forms)} formulários na página")
        for i, form in enumerate(forms):
            print(f"Formulário {i+1}:")
            print(f"  Action: {form.get('action')}")
            print(f"  Method: {form.get('method')}")
    
    # Procurar por links de download
    links = soup.find_all('a', href=True)
    download_links = [link for link in links if 'download' in link.get('href', '').lower()]
    if download_links:
        print(f"Encontrados {len(download_links)} links de download:")
        for link in download_links:
            print(f"  - {link.get('href')}")
    
    # Procurar por iframes
    iframes = soup.find_all('iframe')
    if iframes:
        print(f"Encontrados {len(iframes)} iframes:")
        for iframe in iframes:
            print(f"  - {iframe.get('src')}")
            
    # Imprimir parte do conteúdo para análise
    print("\nConteúdo da página (primeiros 500 caracteres):")
    print(soup.get_text()[:500])
    
except Exception as e:
    print(f"Erro: {e}")