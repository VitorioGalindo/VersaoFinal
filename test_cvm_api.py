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
    response = requests.get(f"{BASE_URL}/cvm/documents?limit=50")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Erro ao fazer requisição: {e}")
    
    # Verificar se o backend está rodando
    try:
        health_check = requests.get(f"http://localhost:{PORT}/health")
        print(f"Health check status: {health_check.status_code}")
    except:
        print("Backend não parece estar rodando. Por favor, inicie-o com 'python run_backend.py'")