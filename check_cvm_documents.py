import psycopg2
from psycopg2 import sql
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

    # Verificar a estrutura da tabela cvm_documents
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'cvm_documents'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    
    if columns:
        print("Estrutura da tabela cvm_documents:")
        print("Column Name\t\tData Type\t\tNullable\tDefault")
        print("-" * 70)
        for col in columns:
            print(f"{col[0]}\t\t\t{col[1]}\t\t{col[2]}\t\t{col[3] or ''}")
    else:
        print("Tabela cvm_documents não encontrada.")
        
    # Verificar se há dados na tabela
    cursor.execute("SELECT COUNT(*) FROM cvm_documents;")
    count = cursor.fetchone()
    print(f"\nTotal de registros na tabela cvm_documents: {count[0]}")
    
    # Verificar alguns registros de exemplo
    if count[0] > 0:
        cursor.execute("SELECT * FROM cvm_documents LIMIT 5;")
        rows = cursor.fetchall()
        print("\nExemplos de registros:")
        for row in rows:
            print(row)
            
    # Verificar tipos de documentos existentes
    cursor.execute("SELECT DISTINCT document_type FROM cvm_documents LIMIT 10;")
    doc_types = cursor.fetchall()
    print("\nTipos de documentos encontrados:")
    for dt in doc_types:
        print(f"- {dt[0]}")

except Exception as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
finally:
    if 'conn' in locals():
        conn.close()