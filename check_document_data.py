import requests
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Configurações da API
PORT = os.getenv('PORT', '5001')
BASE_URL = f"http://localhost:{PORT}/api"

try:
    # Testar a rota que está falhando
    response = requests.get(f"{BASE_URL}/cvm/documents?limit=5")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    
    if 'documents' in data and len(data['documents']) > 0:
        print("Exemplo de documento:")
        doc = data['documents'][0]
        print(f"ID: {doc.get('id')}")
        print(f"Título: {doc.get('title')}")
        print(f"Download URL: {doc.get('download_url')}")
        print(f"Categoria: {doc.get('category')}")
        print(f"Empresa: {doc.get('company_name')}")
        print(f"Data: {doc.get('delivery_date')}")
    else:
        print("Nenhum documento encontrado")
        
except Exception as e:
    print(f"Erro ao fazer requisição: {e}")