import psycopg2
import os
from dotenv import load_dotenv
import re

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Pandora337303$')

def update_document_links():
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
        
        # Selecionar todos os documentos com links de download
        cursor.execute("""
            SELECT id, download_url 
            FROM cvm_documents 
            WHERE download_url LIKE '%frmDownloadDocumento.aspx%'
        """)
        
        documents = cursor.fetchall()
        print(f"Encontrados {len(documents)} documentos para atualizar")
        
        if len(documents) == 0:
            print("Todos os documentos já foram atualizados!")
            return
        
        # Atualizar os links
        updated_count = 0
        duplicate_count = 0
        
        for doc_id, download_url in documents:
            # Extrair o número do protocolo
            protocol_match = re.search(r'NumeroProtocoloEntrega=(\d+)', download_url)
            if protocol_match:
                protocol_number = protocol_match.group(1)
                # Criar o novo link de visualização
                new_url = f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoIPEExterno.aspx?NumeroProtocoloEntrega={protocol_number}"
                
                try:
                    # Atualizar no banco de dados
                    cursor.execute("""
                        UPDATE cvm_documents 
                        SET download_url = %s 
                        WHERE id = %s
                    """, (new_url, doc_id))
                    updated_count += 1
                except psycopg2.IntegrityError as e:
                    # Se houver duplicata, apenas registrar o erro e continuar
                    if "duplicate key value violates unique constraint" in str(e):
                        duplicate_count += 1
                        conn.rollback()  # Reverter a transação
                        print(f"Documento ID {doc_id} ignorado por duplicata: {new_url}")
                    else:
                        raise e  # Re-emitir outros erros
                
                # Mostrar progresso a cada 1000 atualizações
                if (updated_count + duplicate_count) % 1000 == 0:
                    print(f"Atualizados {updated_count}, Ignorados {duplicate_count} documentos...")
                    conn.commit()
        
        # Commit final
        conn.commit()
        print(f"Total de documentos atualizados: {updated_count}")
        print(f"Total de documentos ignorados por duplicata: {duplicate_count}")
        
    except Exception as e:
        print(f"Erro ao atualizar links: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_document_links()