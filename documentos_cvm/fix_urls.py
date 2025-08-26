# fix_urls_sql.py (versão com SQL puro e a função correta regexp_replace)
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import time

# Carrega as variáveis de ambiente
load_dotenv()
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
DB_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Cria a engine de conexão
engine = create_engine(DB_URL)

# O comando SQL que fará toda a mágica diretamente no banco de dados
# Esta versão usa regexp_replace, que é a forma correta e performática para o PostgreSQL
# \1 é uma "back-reference" para o primeiro grupo capturado (o \d+ dentro dos parênteses)
UPDATE_SQL_COMMAND = """
UPDATE public.cvm_documents
SET 
    download_url = regexp_replace(
        download_url, 
        '^.*numProtocolo=(\d+).*$', 
        'https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?NumeroProtocoloEntrega=\\1'
     )
WHERE 
    download_url LIKE '%numProtocolo=%';
"""

def run_sql_migration():
    print("Iniciando a migração de URLs usando SQL puro com regexp_replace. Isso deve ser rápido.")
    start_time = time.time()
    
    try:
        with engine.connect() as connection:
            with connection.begin() as transaction:
                print("Executando o comando UPDATE em massa. Por favor, aguarde...")
                result = connection.execute(text(UPDATE_SQL_COMMAND))
                
                print(f"Comando concluído. O banco de dados processou a atualização.")
                print(f"Total de linhas afetadas: {result.rowcount}")
                
                print("Transação bem-sucedida. Salvando alterações...")
                # O commit é feito automaticamente ao sair do bloco 'with'

        total_time = time.time() - start_time
        print("\n--- MIGRAÇÃO CONCLUÍDA COM SUCESSO ---")
        print(f"Tempo total da operação: {total_time:.2f} segundos.")

    except Exception as e:
        print(f"\n--- ERRO DURANTE A EXECUÇÃO DO SQL ---")
        print(f"Erro: {e}")
        print("Nenhuma alteração foi salva no banco de dados.")

if __name__ == '__main__':
    run_sql_migration()
