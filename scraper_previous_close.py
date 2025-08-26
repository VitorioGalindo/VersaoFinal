#!/usr/bin/env python3
"""
Scraper para obter o fechamento anterior corretamente e popular a coluna previous_close_correct
"""
import sys
import os
import logging
from datetime import datetime
from typing import Optional

# Adicionar o diretório backend ao path para importar os módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_previous_close.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    logger.info("MetaTrader5 disponível")
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 não disponível")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.models import AssetMetrics
from backend.config import Config

def get_previous_close_correct(symbol: str) -> Optional[float]:
    """Obtém o preço de fechamento do pregão anterior corretamente."""
    if not MT5_AVAILABLE:
        logger.debug(f"MT5 não disponível para obter previous_close de {symbol}")
        return None
        
    try:
        logger.debug(f"Tentando obter previous_close correto para {symbol}")
        # Obter dados do dia anterior (TIMEFRAME_D1, 1 barra a partir de 1 posição atrás)
        # Isso nos dá o fechamento do dia útil anterior
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 1, 1)
        logger.debug(f"Dados brutos do MT5 para {symbol} (1 dia atrás): {rates}")
        if rates is not None and len(rates) > 0:
            previous_close = float(rates[0]['close'])
            open_price = float(rates[0]['open'])
            high_price = float(rates[0]['high'])
            low_price = float(rates[0]['low'])
            logger.info(f"Preço de fechamento anterior para {symbol}: {previous_close}")
            logger.debug(f"Preço de abertura do dia anterior para {symbol}: {open_price}")
            logger.debug(f"Preço máximo do dia anterior para {symbol}: {high_price}")
            logger.debug(f"Preço mínimo do dia anterior para {symbol}: {low_price}")
            logger.debug(f"Verificando se são iguais: {previous_close == open_price}")
            return previous_close
        else:
            logger.debug(f"Não obtive dados do MT5 para {symbol} (1 dia atrás)")
            # Tentativa alternativa: obter dados de 2 dias atrás
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 2, 1)
            logger.debug(f"Dados brutos do MT5 para {symbol} (2 dias atrás): {rates}")
            if rates is not None and len(rates) > 0:
                previous_close = float(rates[0]['close'])
                open_price = float(rates[0]['open'])
                high_price = float(rates[0]['high'])
                low_price = float(rates[0]['low'])
                logger.info(f"Preço de fechamento alternativo para {symbol}: {previous_close}")
                logger.debug(f"Preço de abertura do dia alternativo para {symbol}: {open_price}")
                logger.debug(f"Preço máximo do dia alternativo para {symbol}: {high_price}")
                logger.debug(f"Preço mínimo do dia alternativo para {symbol}: {low_price}")
                logger.debug(f"Verificando se são iguais: {previous_close == open_price}")
                return previous_close
            else:
                logger.debug(f"Não obtive dados do MT5 para {symbol} (2 dias atrás)")
    except Exception as e:
        logger.error(f"Erro ao obter preço de fechamento anterior para {symbol}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
    return None

def update_previous_close_correct(engine):
    """Atualiza a coluna previous_close_correct para todos os símbolos."""
    try:
        # Verificar se MT5 está disponível
        if not MT5_AVAILABLE:
            logger.error("MT5 não disponível, não é possível atualizar previous_close_correct")
            return
            
        # Inicializar MT5
        if not mt5.initialize():
            logger.error("Falha ao inicializar MetaTrader5")
            return
            
        logger.info("MetaTrader5 inicializado com sucesso")
        
        # Obter todos os símbolos da tabela asset_metrics
        with engine.connect() as conn:
            result = conn.execute(text("SELECT symbol FROM asset_metrics"))
            symbols = [row[0] for row in result.fetchall()]
            
        logger.info(f"Encontrados {len(symbols)} símbolos para atualizar")
        
        # Atualizar previous_close_correct para cada símbolo
        updated_count = 0
        for symbol in symbols:
            try:
                logger.info(f"Atualizando previous_close_correct para {symbol}")
                previous_close_correct = get_previous_close_correct(symbol)
                
                if previous_close_correct is not None:
                    # Atualizar a coluna previous_close_correct
                    with engine.connect() as conn:
                        conn.execute(text("""
                            UPDATE asset_metrics 
                            SET previous_close_correct = :previous_close_correct 
                            WHERE symbol = :symbol
                        """), {
                            "previous_close_correct": previous_close_correct,
                            "symbol": symbol
                        })
                        conn.commit()
                    logger.info(f"Atualizado previous_close_correct para {symbol}: {previous_close_correct}")
                    updated_count += 1
                else:
                    logger.warning(f"Não foi possível obter previous_close_correct para {symbol}")
                    
            except Exception as e:
                logger.error(f"Erro ao atualizar previous_close_correct para {symbol}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
        logger.info(f"Atualização concluída. {updated_count} símbolos atualizados.")
        
        # Fechar MT5
        mt5.shutdown()
        logger.info("MetaTrader5 encerrado")
        
    except Exception as e:
        logger.error(f"Erro ao atualizar previous_close_correct: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def main():
    """Função principal."""
    try:
        logger.info("Iniciando scraper de previous_close_correct")
        
        # Criar engine de banco de dados
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        logger.info("Conexão com banco de dados estabelecida")
        
        # Atualizar previous_close_correct
        update_previous_close_correct(engine)
        
        logger.info("Scraper de previous_close_correct concluído com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no scraper de previous_close_correct: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()