import os
import sys
from dotenv import load_dotenv
import psycopg2

# Carregar variáveis de ambiente
load_dotenv()

# Obter as variáveis de ambiente do banco de dados
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', '5432')

def check_table_structure():
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        # Verificar a estrutura da tabela research_notes
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'research_notes'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("Estrutura da tabela 'research_notes':")
        print("-" * 50)
        for column in columns:
            print(f"Coluna: {column[0]}, Tipo: {column[1]}, Nullable: {column[2]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_table_structure()