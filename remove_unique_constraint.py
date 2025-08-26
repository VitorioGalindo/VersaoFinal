import psycopg2
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Pandora337303$')

try:
    # Conectar ao banco de dados
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # Remover a restrição de unicidade da coluna download_url
    cursor.execute("""
        ALTER TABLE cvm_documents 
        DROP CONSTRAINT IF EXISTS cvm_documents_download_url_key
    """)
    
    # Commit da alteração
    conn.commit()
    print("Restrição de unicidade removida com sucesso!")
    
except Exception as e:
    print(f"Erro ao remover restrição: {e}")
    if 'conn' in locals():
        conn.rollback()
finally:
    if 'conn' in locals():
        conn.close()