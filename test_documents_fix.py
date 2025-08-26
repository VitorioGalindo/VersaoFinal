import requests
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Configurações da API
PORT = os.getenv('PORT', '5001')
BASE_URL = f"http://localhost:{PORT}/api"

try:
    # Testar a rota com a data de hoje
    today = "2025-08-20"
    response = requests.get(f"{BASE_URL}/cvm/documents?end_date={today}&limit=10")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    
    if 'documents' in data and len(data['documents']) > 0:
        print(f"Encontrados {len(data['documents'])} documentos até {today}:")
        for doc in data['documents']:
            print(f"  Data: {doc.get('delivery_date')}, Título: {doc.get('title')[:50]}...")
    else:
        print("Nenhum documento encontrado")
        
except Exception as e:
    print(f"Erro ao fazer requisição: {e}")