import os
import re
import zipfile
import requests
import pandas as pd
from tqdm import tqdm
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import datetime

from models import Base, CvmDocument, Company

load_dotenv()

# --- Configurações ---
BASE_URL_DFP = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"
BASE_URL_ITR = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"
START_YEAR = 2010
END_YEAR = datetime.date.today().year
BATCH_SIZE = 50000

def get_db_engine():
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    host = os.environ.get("DB_HOST")
    dbname = os.environ.get("DB_NAME")
    if not all([user, password, host, dbname]):
        raise ValueError("Credenciais do banco (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) não encontradas no .env")
    db_url = f"postgresql://{user}:{password}@{host}/{dbname}"
    return create_engine(db_url, pool_pre_ping=True)

def process_and_load_dataframe(session, df, doc_type, report_version, cnpj_to_id_map):
    print(f"    -> Processando {len(df)} linhas para {doc_type}/{report_version}...")
    
    COLUMN_MAPPING = {
        'CNPJ_CIA': 'company_cnpj', 'DT_REFER': 'reference_date', 'VERSAO': 'cvm_version',
        'CD_CONTA': 'account_code', 'DS_CONTA': 'account_name', 'VL_CONTA': 'account_value',
        'MOEDA': 'currency', 'ESCALA_MOEDA': 'currency_scale' # <--- ADICIONADO
    }
    df.rename(columns=COLUMN_MAPPING, inplace=True)
    
    df['company_cnpj'] = df['company_cnpj'].str.replace(r'[./-]', '', regex=True)
    df['company_id'] = df['company_cnpj'].map(cnpj_to_id_map)
    df.dropna(subset=['company_id'], inplace=True)
    df['company_id'] = df['company_id'].astype(int)

    if df.empty:
        print("    -> Nenhum dado válido para as empresas monitoradas encontrado. Pulando.")
        return 0

    df['reference_date'] = pd.to_datetime(df['reference_date'])
    df['account_value'] = pd.to_numeric(df['account_value'], errors='coerce')
    df.dropna(subset=['reference_date', 'account_value'], inplace=True)

    # --- LÓGICA DE PRECISÃO ADICIONADA ---
    def adjust_for_scale(row):
        scale = row.get('currency_scale', 'UNIDADE')
        value = row['account_value']
        if isinstance(scale, str):
            if scale.upper() == 'MIL':
                return value * 1000
            elif scale.upper() == 'MILHÃO':
                return value * 1000000
        return value

    df['account_value'] = df.apply(adjust_for_scale, axis=1)
    # --- FIM DA LÓGICA DE PRECISÃO ---

    df['is_fixed'] = df['account_code'].apply(lambda x: len(str(x).split('.')) <= 2)
    df['report_type'] = doc_type
    df['report_version'] = report_version
    
    model_columns = [c.name for c in CvmDocument.__table__.columns if c.name != 'id']
    df = df[df.columns.intersection(model_columns)]
    
    data_to_insert = df.to_dict(orient='records')

    for i in tqdm(range(0, len(data_to_insert), BATCH_SIZE), desc="      Carregando para o BD"):
        batch = data_to_insert[i:i + BATCH_SIZE]
        try:
            session.bulk_insert_mappings(CvmDocument, batch)
            session.commit()
        except Exception as e:
            print(f"\n      ERRO ao inserir lote: {e}")
            session.rollback()

def download_and_process_zip(session, url, doc_type, cnpj_to_id_map):
    try:
        print(f"\nBaixando arquivo de {url}...")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        zip_path = "temp_financials.zip"
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
        with zipfile.ZipFile(zip_path) as z:
            csv_files = [f for f in z.namelist() if f.endswith(('.csv', '.CSV')) and ('BPA' in f or 'BPP' in f or 'DRE' in f)]
            for filename in csv_files:
                match = re.search(r'_(BPA|BPP|DRE)_(con|ind)_', filename, re.IGNORECASE)
                if not match: continue
                report_version = f"{match.group(1).upper()}_{match.group(2).upper()}"
                print(f"  - Lendo arquivo: {filename} (Versão: {report_version})")
                with z.open(filename) as f:
                    df = pd.read_csv(f, sep=';', encoding='latin1', dtype={'CNPJ_CIA': str, 'CD_CONTA': str})
                    process_and_load_dataframe(session, df, doc_type, report_version, cnpj_to_id_map)
        os.remove(zip_path)
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response and e.response.status_code == 404:
            print(f"AVISO: Arquivo não encontrado (404). Pulando: {url}")
        else:
            print(f"AVISO: Falha no download ou conexão. Pulando: {url}. Erro: {e}")

def run_backfill():
    engine = get_db_engine()
    print("Verificando e criando tabelas no banco de dados, se necessário...")
    Base.metadata.create_all(engine)
    print("Tabelas verificadas/criadas com sucesso.")

    Session = sessionmaker(bind=engine)
    session = Session()

    print("="*80)
    print("🚀 INICIANDO PROCESSO DE BACKFILL DE DADOS FINANCEIROS HISTÓRICOS 🚀")
    print("="*80)
    try:
        print("Limpando a tabela 'cvm_financial_data' para a carga completa...")
        session.execute(text("TRUNCATE TABLE cvm_financial_data RESTART IDENTITY;"))
        session.commit()

        print("Buscando a lista de empresas e criando mapa CNPJ -> ID...")
        companies = session.query(Company).all()
        cnpj_to_id_map = {c.cnpj: c.id for c in companies}
        print(f"Encontradas {len(cnpj_to_id_map)} empresas na tabela 'companies'.")

        if not cnpj_to_id_map:
            print("❌ Nenhuma empresa encontrada para monitorar. Abortando o processo.")
            return

        doc_sources = [{"type": "DFP", "url": BASE_URL_DFP}, {"type": "ITR", "url": BASE_URL_ITR}]
        for year in range(START_YEAR, END_YEAR + 1):
            print(f"\n--- Processando ano: {year} ---")
            for source in doc_sources:
                file_url = f"{source['url']}{source['type'].lower()}_cia_aberta_{year}.zip"
                download_and_process_zip(session, file_url, source['type'], cnpj_to_id_map)

        print("\n" + "="*80)
        print("🎉 PROCESSO DE BACKFILL CONCLUÍDO COM SUCESSO! 🎉")
        print("="*80)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO DURANTE O PROCESSO DE BACKFILL: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
        print("🔌 Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    run_backfill()