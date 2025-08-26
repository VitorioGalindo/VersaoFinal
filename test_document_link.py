import requests
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Configurações da API
PORT = os.getenv('PORT', '5001')
BASE_URL = f"http://localhost:{PORT}/api"

try:
    # Obter um documento de exemplo
    response = requests.get(f"{BASE_URL}/cvm/documents?limit=1")
    data = response.json()
    
    if 'documents' in data and len(data['documents']) > 0:
        doc = data['documents'][0]
        download_url = doc.get('download_url')
        print(f"Download URL: {download_url}")
        
        # Tentar acessar o link diretamente
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        doc_response = requests.get(download_url, headers=headers, allow_redirects=True)
        print(f"Status do link: {doc_response.status_code}")
        print(f"Headers da resposta: {dict(doc_response.headers)}")
        print(f"Tamanho do conteúdo: {len(doc_response.content)} bytes")
    else:
        print("Nenhum documento encontrado")
        
except Exception as e:
    print(f"Erro ao fazer requisição: {e}")