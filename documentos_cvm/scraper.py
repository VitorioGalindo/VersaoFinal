# scraper.py
import os
import requests
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from zipfile import ZipFile
from io import BytesIO
import datetime
import re
from dotenv import load_dotenv

# ... (O início do script, incluindo a configuração do DB_URL, permanece o mesmo) ...
from models import CvmDocument, Company

# --- Configuração ---
load_dotenv() # Carrega as variáveis do arquivo .env para o ambiente

# Pega as credenciais do ambiente
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# Valida se todas as variáveis foram carregadas
if not all([db_host, db_port, db_name, db_user, db_password]):
    raise ValueError("Uma ou mais variáveis de ambiente do banco de dados não foram definidas. Verifique seu arquivo .env.")

# Constrói a DB_URL a partir das variáveis de ambiente
DB_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

START_YEAR = 2003
END_YEAR = datetime.date.today().year
BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{year}.zip"

# --- Conexão com o Banco ---
engine = create_engine(DB_URL )
Session = sessionmaker(bind=engine)


def get_cnpj_to_id_map(session):
    """
    Busca todas as empresas no banco e retorna um dicionário
    mapeando cada CNPJ ao seu ID correspondente.
    """
    print("Mapeando CNPJs para IDs da tabela 'companies'...")
    companies = session.query(Company.id, Company.cnpj).all()
    # Limpa o CNPJ (remove '.', '/' e '-') para uma correspondência robusta
    cnpj_map = {re.sub(r'[^\d]', '', company.cnpj): company.id for company in companies if company.cnpj}
    print(f"{len(cnpj_map)} empresas mapeadas.")
    return cnpj_map

def fetch_and_process_year(year: int, cnpj_map: dict):
    """
    Baixa, extrai e processa o arquivo CSV para um determinado ano,
    utilizando o mapa de CNPJ para ID.
    """
    url = BASE_URL.format(year=year)
    print(f"\nIniciando processamento para o ano: {year}")

    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        with ZipFile(BytesIO(response.content)) as z:
            csv_filename = z.namelist()[0]
            with z.open(csv_filename, 'r') as f:
                df = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip',
                                 dtype={'CNPJ_Companhia': str, 'Codigo_CVM': str})

                # Limpa e mapeia o CNPJ para company_id
                df['CNPJ_Companhia_limpo'] = df['CNPJ_Companhia'].str.replace(r'[^\d]', '', regex=True)
                df['company_id'] = df['CNPJ_Companhia_limpo'].map(cnpj_map)

                original_count = len(df)
                df.dropna(subset=['company_id'], inplace=True)
                if len(df) < original_count:
                    print(f"AVISO: {original_count - len(df)} registros descartados por não terem CNPJ correspondente na tabela 'companies'.")

                rename_map = {
                    'Codigo_CVM': 'cvm_code',
                    'Categoria': 'document_category',
                    'Tipo': 'document_type',
                    'Assunto': 'title',
                    'Data_Entrega': 'delivery_date',
                    'Data_Referencia': 'reference_date',
                    'Link_Download': 'download_url'
                }
                df.rename(columns=rename_map, inplace=True)

                # --- SEÇÃO CORRIGIDA ---
                # 1. Converte colunas de data. `errors='coerce'` transforma falhas em NaT.
                df['delivery_date'] = pd.to_datetime(df['delivery_date'], errors='coerce')
                df['reference_date'] = pd.to_datetime(df['reference_date'], errors='coerce')

                # 2. Remove explicitamente as linhas onde a conversão de data falhou (resultou em NaT)
                #    ou onde outras colunas essenciais são nulas.
                df.dropna(subset=['delivery_date', 'reference_date', 'download_url', 'cvm_code'], inplace=True)
                # --- FIM DA SEÇÃO CORRIGIDA ---

                # Seleciona apenas as colunas que vamos usar
                columns_to_keep = list(rename_map.values()) + ['company_id']
                df = df[columns_to_keep]

                # Garante tipos corretos antes de inserir
                df['company_id'] = df['company_id'].astype(int)
                df['cvm_code'] = pd.to_numeric(df['cvm_code'], errors='coerce').astype('Int64') # Converte para numérico e depois para Int64 para segurança

                data_to_insert = df.to_dict(orient='records')
                save_to_db(data_to_insert)

                
                df['protocolo'] = df['Link_Download'].str.extract(r'numProtocolo=(\d+)', expand=False)
                df['download_url'] = 'https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?NumeroProtocoloEntrega=' + df['protocolo']
                rename_map = {
                        'Codigo_CVM': 'cvm_code',
                        'Categoria': 'document_category',
                        'Tipo': 'document_type',     
                        'Assunto': 'title',
                        'Data_Entrega': 'delivery_date',
                        'Data_Referencia': 'reference_date',
                        # Não precisamos mais mapear 'Link_Download', pois já criamos 'download_url'
                }
                df.rename(columns=rename_map, inplace=True )


                        

        print(f"Ano {year} processado. {len(data_to_insert)} registros lidos e válidos.")

    except requests.exceptions.RequestException as e:
        print(f"ERRO ao baixar dados para o ano {year}: {e}")
    except Exception as e:
        print(f"ERRO inesperado ao processar o ano {year}: {e}")


def save_to_db(data: list[dict]):
    """
    Salva uma lista de registros no banco, ignorando duplicatas pelo 'download_url'.
    """
    if not data:
        return

    session = Session()
    try:
        urls_in_payload = [d['download_url'] for d in data]
        query = session.query(CvmDocument.download_url).filter(CvmDocument.download_url.in_(urls_in_payload))
        existing_urls = {res[0] for res in query}
        
        new_documents = []
        for item in data:
            if item['download_url'] not in existing_urls:
                new_documents.append(CvmDocument(**item))

        if new_documents:
            session.bulk_save_objects(new_documents)
            session.commit()
            print(f"SUCESSO: {len(new_documents)} novos registros inseridos no banco.")
        else:
            # Verifica se havia dados para inserir mas todos já existiam
            if data:
                print("Nenhum registro novo para inserir (todos já existem no DB).")
            
    except Exception as e:
        session.rollback()
        print(f"ERRO ao salvar no banco de dados: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    main_session = Session()
    try:
        cnpj_id_map = get_cnpj_to_id_map(main_session)
    finally:
        main_session.close()

    if not cnpj_id_map:
        print("ERRO CRÍTICO: Não foi possível carregar o mapa de CNPJ-ID. Verifique a tabela 'companies'. Abortando.")
    else:
        # Como os dados até 2018 já foram inseridos, você pode começar a partir de 2019 para economizar tempo
        # Altere o START_YEAR aqui se desejar
        for year in range(START_YEAR, END_YEAR + 1):
            fetch_and_process_year(year, cnpj_id_map)
        print("\nProcesso de scraping concluído.")

