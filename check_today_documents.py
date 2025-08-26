import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

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
    
    # Verificar documentos de hoje
    today = datetime.now().date()
    tomorrow = datetime(today.year, today.month, today.day + 1) if today.day < 31 else datetime(today.year, today.month + 1, 1) if today.month < 12 else datetime(today.year + 1, 1, 1)
    
    print(f"Data de hoje: {today}")
    print(f"Amanhã: {tomorrow.date()}")
    
    # Buscar documentos de hoje
    cursor.execute("""
        SELECT id, delivery_date, title 
        FROM cvm_documents 
        WHERE delivery_date >= %s AND delivery_date < %s
        ORDER BY delivery_date DESC
        LIMIT 10
    """, (today, tomorrow))
    
    today_docs = cursor.fetchall()
    print(f"\nDocumentos de hoje ({len(today_docs)} encontrados):")
    for doc in today_docs:
        print(f"  ID: {doc[0]}, Data: {doc[1]}, Título: {doc[2][:50]}...")
        
    # Buscar documentos com a data de hoje usando o filtro <=
    cursor.execute("""
        SELECT id, delivery_date, title 
        FROM cvm_documents 
        WHERE delivery_date <= %s
        ORDER BY delivery_date DESC
        LIMIT 10
    """, (today,))
    
    docs_until_today = cursor.fetchall()
    print(f"\nDocumentos até hoje (usando <= {today}) ({len(docs_until_today)} encontrados):")
    for doc in docs_until_today:
        print(f"  ID: {doc[0]}, Data: {doc[1]}, Título: {doc[2][:50]}...")
        
except Exception as e:
    print(f"Erro: {e}")
finally:
    if 'conn' in locals():
        conn.close()