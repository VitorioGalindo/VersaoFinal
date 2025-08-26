import os
import sys
import time
import pandas as pd
import MetaTrader5 as mt5
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from tqdm import tqdm
import logging

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
load_dotenv()

def get_db_engine():
    """Cria e retorna a engine do SQLAlchemy para o PostgreSQL."""
    try:
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME")
        
        ssl_mode = 'prefer' if db_host in ('localhost', '127.0.0.1') else 'require'
        db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}?sslmode={ssl_mode}"
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logging.info("✅ Conexão com o banco de dados estabelecida com sucesso.")
        return engine
    except Exception as e:
        logging.error(f"❌ Falha ao conectar ao banco de dados: {e}")
        raise

def connect_mt5():
    """Conecta-se ao MetaTrader 5."""
    try:
        mt5_login = int(os.getenv("MT5_LOGIN"))
        mt5_password = os.getenv("MT5_PASSWORD")
        mt5_server = os.getenv("MT5_SERVER")

        if not mt5.initialize(login=mt5_login, password=mt5_password, server=mt5_server):
            raise ConnectionError(f"Falha ao inicializar o MT5: {mt5.last_error()}")
        logging.info(f"✅ Conectado ao MetaTrader 5 com sucesso (Conta: {mt5_login}).")
        return True
    except Exception as e:
        logging.error(f"❌ Falha ao conectar ao MetaTrader 5: {e}")
        raise

def get_all_tickers_from_db(engine):
    """Busca a lista de todos os símbolos da nossa tabela 'tickers'."""
    logging.info("Buscando lista de todos os tickers do banco de dados...")
    try:
        df_tickers = pd.read_sql("SELECT symbol FROM tickers", engine)
        tickers = df_tickers['symbol'].tolist()
        logging.info(f"Encontrados {len(tickers)} tickers para processar.")
        return tickers
    except Exception as e:
        logging.error(f"❌ Não foi possível buscar tickers do banco: {e}")
        return []

def main():
    """Função principal que orquestra o processo de scraping."""
    logging.info("🚀 Iniciando o Scraper Universal de Dados do MT5...")
    engine = None
    
    try:
        engine = get_db_engine()
        connect_mt5()
        
        all_symbols = get_all_tickers_from_db(engine)
        if not all_symbols:
            logging.warning("Nenhum ticker encontrado. Encerrando.")
            return

        all_metrics = []
        for symbol in tqdm(all_symbols, desc="Processando Ativos"):
            if not mt5.symbol_select(symbol, True):
                continue
            
            info = mt5.symbol_info(symbol)
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 2)

            if not info or rates is None or len(rates) < 2:
                continue

            today = rates[1]
            yesterday = rates[0]
            
            change = today['close'] - yesterday['close']
            change_percent = (change / yesterday['close']) * 100 if yesterday['close'] > 0 else 0

            all_metrics.append({
                "symbol": symbol,
                "description": info.description,
                "sector": getattr(info, 'sector', 'N/A'),
                "industry": getattr(info, 'industry', 'N/A'),
                "last_price": today['close'],
                "previous_close": yesterday['close'],
                "price_change": change,
                "price_change_percent": change_percent,
                "volume": today['real_volume'],
                "open_price": today['open'],
                "high_price": today['high'],
                "low_price": today['low'],
                "updated_at": pd.to_datetime(today['time'], unit='s')
            })

        if not all_metrics:
            logging.info("Nenhuma métrica coletada.")
            return

        logging.info(f"Coletadas métricas para {len(all_metrics)} ativos. Atualizando banco de dados...")
        df_metrics = pd.DataFrame(all_metrics)

        # --- CORREÇÃO FINAL AQUI ---
        # Convertemos a coluna 'volume' para um tipo compatível com o PostgreSQL.
        df_metrics['volume'] = df_metrics['volume'].astype('int64')

        # Usando o padrão de UPSERT via tabela temporária para máxima eficiência
        with engine.connect() as conn:
            df_metrics.to_sql('temp_asset_metrics', conn, if_exists='replace', index=False)
            upsert_sql = text("""
                INSERT INTO asset_metrics (symbol, description, sector, industry, last_price, previous_close, price_change, price_change_percent, volume, open_price, high_price, low_price, updated_at)
                SELECT symbol, description, sector, industry, last_price, previous_close, price_change, price_change_percent, volume, open_price, high_price, low_price, updated_at
                FROM temp_asset_metrics
                ON CONFLICT (symbol) DO UPDATE
                SET 
                    description = EXCLUDED.description,
                    sector = EXCLUDED.sector,
                    industry = EXCLUDED.industry,
                    last_price = EXCLUDED.last_price,
                    previous_close = EXCLUDED.previous_close,
                    price_change = EXCLUDED.price_change,
                    price_change_percent = EXCLUDED.price_change_percent,
                    volume = EXCLUDED.volume,
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    updated_at = EXCLUDED.updated_at;
            """)
            conn.execute(upsert_sql)
            conn.commit()
        logging.info("✅ Banco de dados atualizado com sucesso!")

    except Exception as e:
        logging.critical(f"Um erro fatal ocorreu: {e}")
    finally:
        mt5.shutdown()
        logging.info("Conexão com o MetaTrader 5 encerrada.")
        logging.info("🏁 Scraper finalizado.")

if __name__ == "__main__":
    main()