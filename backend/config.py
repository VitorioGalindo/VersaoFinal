# backend/config.py
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  # Carrega variáveis do arquivo .env
logger = logging.getLogger(__name__)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-padrao-muito-segura'

    # Configurações do SQLAlchemy
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_NAME = os.environ.get('DB_NAME')
    
    # --- LÓGICA CORRIGIDA AQUI ---
    # Verifica se o host do banco é local. Se for, não exige SSL.
    # Se for um endereço externo (nuvem), exige SSL para segurança.
    if DB_HOST in ('localhost', '127.0.0.1'):
        # Para banco de dados local, o sslmode 'prefer' tenta usar SSL
        # mas não falha se o servidor não o suportar.
        ssl_mode = 'prefer' 
    else:
        # Para bancos de dados na nuvem (AWS RDS), sempre exigir SSL.
        ssl_mode = 'require'

    # Monta a URI de conexão com o ssl_mode dinâmico
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}/{DB_NAME}?sslmode={ssl_mode}"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

def get_db_engine():
    """
    Cria e retorna uma engine do SQLAlchemy baseada na URI de configuração.
    Esta função centraliza a criação da engine para ser usada por scripts
    e outras partes da aplicação que não estão diretamente no contexto do Flask.
    """
    uri = Config.SQLALCHEMY_DATABASE_URI
    if uri.startswith('sqlite'):
        print("AVISO: get_db_engine está usando o banco de dados em memória (SQLite) de fallback.")

    try:
        engine = create_engine(uri, pool_pre_ping=True)
    except Exception as exc:
        logger.exception("Falha ao criar a engine do banco de dados.")
        raise

    return engine