import requests
import webbrowser
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
    
    # Se for um documento PDF ou similar, podemos salvá-lo
    content_type = response.headers.get('Content-Type', '')
    if 'pdf' in content_type.lower() or 'octet-stream' in content_type.lower():
        print("Este é um documento para download")
        # Salvar temporariamente para testar
        with open('test_document.pdf', 'wb') as f:
            f.write(response.content)
        print("Documento salvo como test_document.pdf")
    else:
        print("Este é uma página HTML")
        print(f"Tamanho da resposta: {len(response.content)} bytes")
        
except Exception as e:
    print(f"Erro: {e}")

# Tentar abrir no browser
print("\nTentando abrir no browser...")
webbrowser.open(download_url)