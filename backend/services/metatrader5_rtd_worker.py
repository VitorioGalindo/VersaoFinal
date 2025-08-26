# backend/services/metatrader5_rtd_worker.py
# Real-Time Data Worker integrado com MetaTrader5 para cotações do mercado brasileiro
# VERSÃO TEMPO REAL - FOCO EM TICKS EM TEMPO REAL

import os
import sys
import time
import threading
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    logger.info("MetaTrader5 disponível")
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 não disponível - conexão MT5 inativa")

class MetaTrader5RTDWorker:
    """
    Worker para cotações tempo real usando MetaTrader5
    FOCO EM TICKS EM TEMPO REAL
    """

    def __init__(self, socketio=None):
        self.socketio = socketio
        self.running = False
        self.mt5_connected = False
        self.active_subscriptions: Dict[str, Set[str]] = {}
        self.ticker_prices: Dict[str, Dict] = {}
        self.db_engine = None
        self.worker_thread = None
        self.mt5_symbols: Set[str] = set()
        self.realtime_symbols: Set[str] = set()  # Símbolos com ticks em tempo real
        self.failed_symbols: Set[str] = set()    # Símbolos que falharam na ativação
        self.activation_failures: Dict[str, int] = {}

        # Símbolos principais a serem ativados ao iniciar
        self.main_symbols: List[str] = [
            'VALE3', 'PETR4', 'ITUB4', 'BBDC4', 'ABEV3',
            'MGLU3', 'WEGE3', 'RENT3', 'LREN3', 'BOVA11'
        ]

        # Limite para tentativas de ativação de tempo real por símbolo
        self.MAX_ACTIVATION_RETRIES = 3

        # Carrega variáveis do arquivo .env
        load_dotenv()

        # Configurações do MetaTrader5
        self.MT5_LOGIN = int(os.getenv("MT5_LOGIN", "5223688"))
        self.MT5_PASSWORD = os.getenv("MT5_PASSWORD", "SENHA_DEFAULT")
        self.MT5_SERVER = os.getenv("MT5_SERVER", "SERVIDOR_DEFAULT")

        if "MT5_LOGIN" not in os.environ:
            logger.warning("MT5_LOGIN ausente; usando valor padrão")
        if "MT5_PASSWORD" not in os.environ:
            logger.warning("MT5_PASSWORD ausente; usando valor padrão")
        if "MT5_SERVER" not in os.environ:
            logger.warning("MT5_SERVER ausente; usando valor padrão")
        
        # Configurações de timing
        self.PAUSE_INTERVAL_SECONDS = 1  # Atualizar a cada 1 segundo para tempo real
        self.RETRY_DELAY_SECONDS = 30

        # Inicializar conexão com banco
        self._initialize_database()

    def _initialize_database(self):
        """Inicializa conexão com PostgreSQL."""
        try:
            load_dotenv()
            db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"
            self.db_engine = create_engine(db_url, pool_pre_ping=True)
            
            # Testar conexão
            with self.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Conexão com banco PostgreSQL estabelecida")
        except Exception as e:
            logger.error(f"Erro ao conectar com PostgreSQL: {e}")
            self.db_engine = None

    def initialize_mt5(self):
        """Inicializa conexão com MetaTrader5."""
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 não disponível")
            raise RuntimeError("MetaTrader5 não disponível")

        try:
            if not mt5.initialize(
                login=self.MT5_LOGIN,
                password=self.MT5_PASSWORD,
                server=self.MT5_SERVER,
            ):
                logger.error(
                    f"Falha ao inicializar MetaTrader5: {mt5.last_error()}"
                )
                raise RuntimeError(
                    f"Falha ao inicializar MetaTrader5: {mt5.last_error()}"
                )

            logger.info(f"Login MT5 realizado com sucesso: {self.MT5_LOGIN}")

            # Sincronizar símbolos e ativar tempo real
            self._sync_symbols_realtime()

            self.mt5_connected = True
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar MT5: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Erro ao inicializar MT5: {e}")

    def _sync_symbols_realtime(self):
        """Sincroniza símbolos e ativa tempo real para principais."""
        try:
            symbols = mt5.symbols_get()
            if symbols:
                self.mt5_symbols = {symbol.name for symbol in symbols}
                logger.info(f"Sincronizando {len(self.mt5_symbols)} símbolos...")
                
                # Ativar tempo real para símbolos principais IMEDIATAMENTE
                logger.info("Ativando tempo real para símbolos principais...")
                for symbol in list(self.main_symbols):
                    if symbol not in self.mt5_symbols:
                        continue
                    try:
                        success = self._activate_realtime_for_symbol(symbol)
                        if not success:
                            attempts = self.activation_failures.get(symbol, 0) + 1
                            self.activation_failures[symbol] = attempts
                            if attempts >= self.MAX_ACTIVATION_RETRIES:
                                self.main_symbols.remove(symbol)
                                logger.warning(
                                    f"{symbol}: removido após {attempts} falhas de ativação"
                                )
                    except Exception as e:
                        attempts = self.activation_failures.get(symbol, 0) + 1
                        self.activation_failures[symbol] = attempts
                        logger.error(f"Erro ao ativar tempo real para {symbol}: {e}")
                        if attempts >= self.MAX_ACTIVATION_RETRIES:
                            self.main_symbols.remove(symbol)
                            logger.warning(
                                f"{symbol}: removido após {attempts} falhas de ativação"
                            )
                
                logger.info(f"Tempo real ativo para: {list(self.realtime_symbols)}")
                logger.info(f"Falha na ativação: {list(self.failed_symbols)}")
                
            else:
                logger.warning("Nenhum símbolo encontrado no Market Watch")
                
        except Exception as e:
            logger.error(f"Erro ao sincronizar símbolos: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _activate_realtime_for_symbol(self, symbol: str):
        """Ativa tempo real para um símbolo específico usando market_book_add."""
        try:
            # Primeiro tentar symbol_select
            if mt5.symbol_select(symbol, True):
                tick = mt5.symbol_info_tick(symbol)
                if tick and tick.bid > 0:
                    self.realtime_symbols.add(symbol)
                    logger.info(f"{symbol}: tempo real ativo via symbol_select")
                    return True
            
            # Se symbol_select não funcionar, tentar market_book_add
            if mt5.market_book_add(symbol):
                tick = mt5.symbol_info_tick(symbol)
                if tick and tick.bid > 0:
                    self.realtime_symbols.add(symbol)
                    logger.info(f"{symbol}: tempo real ativo via market_book_add")
                    return True
                    
            self.failed_symbols.add(symbol)
            logger.warning(f"{symbol}: falha na ativação de tempo real")
            return False

        except Exception as e:
            self.failed_symbols.add(symbol)
            logger.error(f"{symbol}: erro ao ativar tempo real: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    # --- Legacy compatibility methods ---
    def initialize(self):
        """Alias para initialize_mt5 para compatibilidade retroativa."""
        return self.initialize_mt5()

    def activate_realtime_for_symbol(self, symbol: str):
        """Alias para _activate_realtime_for_symbol para compatibilidade retroativa."""
        return self._activate_realtime_for_symbol(symbol)

    def get_mt5_quote(self, ticker: str) -> Optional[Dict]:
        """
        Obtém cotação EM TEMPO REAL do MetaTrader5, agora enriquecida
        com dados diários (OHLC e Fechamento Anterior).
        """
        if not self.mt5_connected or not MT5_AVAILABLE:
            logger.error(f"❌ MT5 não conectado. Não é possível obter cotação para {ticker}")
            return None

        try:
            if ticker not in self.mt5_symbols:
                logger.warning(f"⚠️ Ticker '{ticker}' não encontrado")
                return None

            # --- NOVO: LÓGICA PARA BUSCAR DADOS DIÁRIOS (OHLC) ---
            daily_data = {
                'open': 0.0,
                'high': 0.0,
                'low': 0.0,
                'previous_close': 0.0
            }
            rates_d1 = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_D1, 0, 2)
            if rates_d1 is not None and len(rates_d1) == 2:
                # rates_d1[0] é o candle de ontem (D-1)
                # rates_d1[1] é o candle de hoje (D)
                daily_data['previous_close'] = rates_d1[0]['close']
                daily_data['open'] = rates_d1[1]['open']
                daily_data['high'] = rates_d1[1]['high']
                daily_data['low'] = rates_d1[1]['low']
            elif rates_d1 is not None and len(rates_d1) == 1:
                 # Se só temos o candle de hoje, não temos o fechamento anterior por este método
                 daily_data['open'] = rates_d1[0]['open']
                 daily_data['high'] = rates_d1[0]['high']
                 daily_data['low'] = rates_d1[0]['low']

            # --- LÓGICA EXISTENTE PARA BUSCAR O TICK EM TEMPO REAL ---
            
            # PRIORIDADE 1: Se já tem tempo real ativo, usar tick
            if ticker in self.realtime_symbols:
                tick = mt5.symbol_info_tick(ticker)
                if tick and tick.bid > 0:
                    # MODIFICADO: Passar os dados diários para a função de formatação
                    return self._format_realtime_quote(ticker, tick, daily_data)
                else:
                    logger.warning(f"⚠️ {ticker}: tempo real ativo, mas tick inválido")
            
            # PRIORIDADE 2: Tentar ativar tempo real AGORA
            if ticker not in self.failed_symbols:
                if self._activate_realtime_for_symbol(ticker):
                    tick = mt5.symbol_info_tick(ticker)
                    if tick and tick.bid > 0:
                        # MODIFICADO: Passar os dados diários
                        return self._format_realtime_quote(ticker, tick, daily_data)
            
            # PRIORIDADE 3: Tentar forçar tick sem ativação
            tick = mt5.symbol_info_tick(ticker)
            if tick and tick.bid > 0:
                logger.info(f"✅ {ticker}: Tick obtido sem ativação prévia")
                # MODIFICADO: Passar os dados diários
                return self._format_realtime_quote(ticker, tick, daily_data)
            
            # ÚLTIMO RECURSO: Dados mais recentes possíveis (M1)
            logger.warning(f"⚠️ {ticker}: usando dados M1 como último recurso")
            rates_m1 = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_M1, 0, 1)
            if rates_m1 is not None and len(rates_m1) > 0:
                rate = rates_m1[0]
                # MODIFICADO: Passar os dados diários aqui também
                quote = self._format_quote_from_rate(ticker, rate, "M1_fallback")
                quote.update(daily_data) # Adicionar dados diários ao fallback
                return quote

            logger.error(f"❌ {ticker}: nenhum tick válido encontrado")
            return None

        except Exception as e:
            logger.error(f"❌ Erro ao obter cotação para {ticker}: {e}")
            return None

    def _format_realtime_quote(self, ticker: str, tick, daily_data: dict) -> Dict:
        """
        Formata cotação em tempo real, agora incluindo dados OHLC e previous_close.
        """
        price = tick.last if tick.last > 0 else tick.bid
        
        # MODIFICADO: Adicionado os novos campos do daily_data
        return {
            "symbol": ticker,
            "bid": float(tick.bid),
            "ask": float(tick.ask),
            "last": float(tick.last),
            "price": float(price), # Preço atual para cálculo de variação
            "volume": int(tick.volume),
            "time": datetime.fromtimestamp(tick.time).isoformat(),
            "source": "mt5_realtime",
            "flags": tick.flags,
            "volume_real": float(getattr(tick, 'volume_real', 0)),
            "is_realtime": True,
            # --- NOVOS CAMPOS ADICIONADOS ---
            "open": float(daily_data.get('open', 0.0)),
            "high": float(daily_data.get('high', 0.0)),
            "low": float(daily_data.get('low', 0.0)),
            "previous_close": float(daily_data.get('previous_close', 0.0))
        }

        
        logger.debug(f"Dados formatados para {ticker}:")
        logger.debug(f"  last: {result['last']}")
        logger.debug(f"  previous_close: {result['previous_close']}")
        logger.debug(f"  open_price: {result['open_price']}")
        logger.debug(f"  price_change: {result['price_change']:.4f}")
        logger.debug(f"  price_change_percent: {result['price_change_percent']:.4f}%")
        logger.debug(f"  VERIFICANDO TROCA - previous_close == open_price? {result['previous_close'] == result['open_price']}")
        
        logger.debug(f"Formatted realtime quote for {ticker}: {result}")
        return result

    def _get_previous_close(self, ticker: str) -> Optional[float]:
        """Obtém o preço de fechamento do pregão anterior."""
        if not self.mt5_connected or not MT5_AVAILABLE:
            logger.debug(f"MT5 não conectado para obter previous_close de {ticker}")
            return None
            
        try:
            logger.debug(f"Tentando obter previous_close para {ticker}")
            # Obter dados do dia anterior (TIMEFRAME_D1, 1 barra a partir de 1 posição atrás)
            # Isso nos dá o fechamento do dia útil anterior
            rates = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_D1, 1, 1)
            logger.debug(f"Dados brutos do MT5 para {ticker} (1 dia atrás): {rates}")
            if rates is not None and len(rates) > 0:
                previous_close = float(rates[0]['close'])
                open_price = float(rates[0]['open'])
                high_price = float(rates[0]['high'])
                low_price = float(rates[0]['low'])
                logger.debug(f"Preço de fechamento anterior para {ticker}: {previous_close}")
                logger.debug(f"Preço de abertura do dia anterior para {ticker}: {open_price}")
                logger.debug(f"Preço máximo do dia anterior para {ticker}: {high_price}")
                logger.debug(f"Preço mínimo do dia anterior para {ticker}: {low_price}")
                logger.debug(f"Verificando se são iguais: {previous_close == open_price}")
                return previous_close
            else:
                logger.debug(f"Não obtive dados do MT5 para {ticker} (1 dia atrás)")
                # Tentativa alternativa: obter dados de 2 dias atrás
                rates = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_D1, 2, 1)
                logger.debug(f"Dados brutos do MT5 para {ticker} (2 dias atrás): {rates}")
                if rates is not None and len(rates) > 0:
                    previous_close = float(rates[0]['close'])
                    open_price = float(rates[0]['open'])
                    high_price = float(rates[0]['high'])
                    low_price = float(rates[0]['low'])
                    logger.debug(f"Preço de fechamento alternativo para {ticker}: {previous_close}")
                    logger.debug(f"Preço de abertura do dia alternativo para {ticker}: {open_price}")
                    logger.debug(f"Preço máximo do dia alternativo para {ticker}: {high_price}")
                    logger.debug(f"Preço mínimo do dia alternativo para {ticker}: {low_price}")
                    logger.debug(f"Verificando se são iguais: {previous_close == open_price}")
                    return previous_close
                else:
                    logger.debug(f"Não obtive dados do MT5 para {ticker} (2 dias atrás)")
        except Exception as e:
            logger.error(f"Erro ao obter preço de fechamento anterior para {ticker}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
        return None

    def _format_quote_from_rate(self, ticker: str, rate, source: str) -> Dict:
        """Formata cotação a partir de dados históricos (último recurso)."""
        close_price = float(rate['close'])
        open_price = float(rate['open'])
        
        # Obter o preço de fechamento anterior corretamente
        previous_close = self._get_previous_close(ticker)
        logger.debug(f"Dados históricos para {ticker}: close={close_price}, open={open_price}, previous_close={previous_close}")
        
        price_change = 0
        price_change_percent = 0
        if previous_close is not None and previous_close > 0:
            price_change = close_price - previous_close
            price_change_percent = (price_change / previous_close * 100)
            logger.debug(f"Calculando variação para {ticker}: close={close_price}, previous_close={previous_close}, change={price_change:.4f}, change_percent={price_change_percent:.4f}%")
        else:
            logger.debug(f"Não foi possível calcular variação para {ticker}: previous_close={previous_close}")
        
        result = {
            "symbol": ticker,
            "bid": close_price,
            "ask": close_price,
            "last": close_price,
            "volume": int(rate['tick_volume']),
            "time": datetime.fromtimestamp(rate['time']).isoformat(),
            "source": source,
            "price": close_price,
            "open_price": open_price,
            "high_price": float(rate['high']),
            "low_price": float(rate['low']),
            "is_realtime": False,
            "price_change": price_change,
            "price_change_percent": price_change_percent
        }
        
        logger.debug(f"Dados formatados para {ticker} (histórico):")
        logger.debug(f"  last: {result['last']}")
        logger.debug(f"  previous_close: {previous_close}")
        logger.debug(f"  open_price: {result['open_price']}")
        logger.debug(f"  price_change: {result['price_change']:.4f}")
        logger.debug(f"  price_change_percent: {result['price_change_percent']:.4f}%")
        logger.debug(f"  VERIFICANDO TROCA - previous_close == open_price? {previous_close == result['open_price']}")

    def _price_update_loop(self):
        """Loop principal para atualização de preços EM TEMPO REAL."""
        logger.info("Iniciando loop de atualização TEMPO REAL...")
        
        while self.running:
            try:
                if self.mt5_connected:
                    # Obter todos os símbolos da carteira e símbolos principais
                    portfolio_symbols = self._get_portfolio_symbols()
                    all_symbols = set(list(self.main_symbols) + portfolio_symbols)
                    
                    # Atualizar preços dos tickers subscritos e da carteira
                    active_symbols = set()
                    
                    # Adicionar símbolos ativos por subscrição
                    for room, tickers in self.active_subscriptions.items():
                        active_symbols.update(tickers)
                    
                    # Combinar todos os símbolos que precisam ser monitorados
                    symbols_to_monitor = all_symbols.union(active_symbols)
                    
                    logger.debug(f"Símbolos a monitorar: {symbols_to_monitor}")
                    logger.debug(f"Símbolos da carteira: {portfolio_symbols}")
                    logger.debug(f"Símbolos principais: {self.main_symbols}")
                    logger.debug(f"Símbolos ativos por subscrição: {active_symbols}")
                    logger.debug(f"Subscrições ativas: {self.active_subscriptions}")
                    
                    # Atualizar preços para todos os símbolos
                    updated_count = 0
                    for symbol in symbols_to_monitor:
                        logger.debug(f"Processing symbol: {symbol}")
                        quote = self.get_mt5_quote(symbol)
                        if quote:
                            logger.debug(f"Got quote for {symbol}: {quote}")
                            # Enviar via WebSocket para subscrições ativas
                            if self.socketio and active_symbols and symbol in active_symbols:
                                logger.debug(f"Enviando atualização para {symbol}")
                                for room, tickers in self.active_subscriptions.items():
                                    if symbol in tickers:
                                        logger.debug(f"Enviando dados para room {room}")
                                        # Enviar dados no formato esperado pelo frontend
                                        self.socketio.emit('price_update', quote, room=room)
                            
                            # Atualizar no banco de dados
                            self._update_asset_metrics(quote)
                            updated_count += 1
                        else:
                            logger.debug(f"No quote available for {symbol}")
                    
                    if updated_count > 0:
                        logger.info(f"Atualizados {updated_count} ativos em tempo real")
                
                time.sleep(self.PAUSE_INTERVAL_SECONDS)  # 1 segundo para tempo real
                
            except Exception as e:
                logger.error(f"Erro no loop de atualização: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                time.sleep(self.RETRY_DELAY_SECONDS)

    def _get_portfolio_symbols(self) -> List[str]:
        """Obtém todos os símbolos que estão nas posições da carteira."""
        if not self.db_engine:
            logger.warning("Database engine não disponível para obter símbolos da carteira")
            return []
            
        try:
            from sqlalchemy import text
            
            query = text("""
                SELECT DISTINCT symbol 
                FROM portfolio_positions 
                WHERE quantity > 0
            """)
            
            with self.db_engine.connect() as conn:
                result = conn.execute(query)
                symbols = [row[0] for row in result.fetchall()]
                
            logger.info(f"Encontrados {len(symbols)} símbolos na carteira: {symbols}")
            return symbols
            
        except Exception as e:
            logger.error(f"Erro ao obter símbolos da carteira: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def _update_asset_metrics(self, quote: Dict):
        """Atualiza os dados de AssetMetrics no banco de dados."""
        if not self.db_engine:
            logger.warning("Database engine não disponível para atualização de métricas")
            return
            
        try:
            from sqlalchemy import text
            
            symbol = quote["symbol"]
            logger.debug(f"Atualizando AssetMetrics para {symbol}")
            
            # Verificar se o ticker existe na tabela tickers
            check_ticker_sql = text("SELECT COUNT(*) FROM tickers WHERE symbol = :symbol")
            with self.db_engine.connect() as conn:
                result = conn.execute(check_ticker_sql, {"symbol": symbol})
                count = result.scalar()
                
                if count == 0:
                    # Se o ticker não existe, inserir na tabela tickers
                    insert_ticker_sql = text("""
                        INSERT INTO tickers (symbol, type, company_id) 
                        VALUES (:symbol, 'STOCK', NULL)
                        ON CONFLICT (symbol) DO NOTHING
                    """)
                    conn.execute(insert_ticker_sql, {"symbol": symbol})
                
                # Calcular variações de preço usando o fechamento anterior
                last_price = float(quote.get("last", 0))
                logger.debug(f"Last price para {symbol}: {last_price}")
                
                # Obter o previous_close corretamente (usando a nova coluna corrigida)
                previous_close = None
                if "previous_close" in quote and quote["previous_close"] is not None:
                    previous_close = float(quote["previous_close"])
                    logger.debug(f"Previous close do quote para {symbol}: {previous_close}")
                    # Verificar se o previous_close é realmente o fechamento anterior ou se é o open_price
                    open_price_check = float(quote.get("open_price", 0)) if quote.get("open_price") is not None else 0
                    last_price_check = float(quote.get("last", 0)) if quote.get("last") is not None else 0
                    logger.debug(f"Verificação - {symbol}: previous_close={previous_close}, open_price={open_price_check}, last_price={last_price_check}")
                    logger.debug(f"Suspeita de troca - {symbol}: previous_close == open_price? {previous_close == open_price_check}")
                
                # Se não tivermos o previous_close no quote, tentar obter do banco de dados (usando a nova coluna corrigida)
                if previous_close is None or previous_close <= 0:
                    try:
                        get_previous_close_sql = text("""
                            SELECT previous_close_correct FROM asset_metrics WHERE symbol = :symbol
                        """)
                        result = conn.execute(get_previous_close_sql, {"symbol": symbol})
                        row = result.fetchone()
                        if row and row[0] is not None:
                            previous_close = float(row[0])
                            logger.debug(f"Previous close corrigido do banco para {symbol}: {previous_close}")
                    except Exception as e:
                        logger.debug(f"Erro ao obter previous_close_corrigido do banco para {symbol}: {e}")
                
                # Se ainda não tivermos o previous_close, tentar obter do MT5
                if previous_close is None or previous_close <= 0:
                    previous_close = self._get_previous_close(symbol)
                    if previous_close is not None and previous_close > 0:
                        logger.debug(f"Obtido previous_close do MT5 para {symbol}: {previous_close}")
                    else:
                        logger.debug(f"Não foi possível obter previous_close para {symbol}")
                
                # Calcular a variação percentual usando o fechamento anterior
                price_change = 0
                price_change_percent = 0
                open_price = float(quote.get("open_price", 0))
                logger.debug(f"Open price para {symbol}: {open_price}")
                logger.debug(f"Last price para {symbol}: {last_price}")
                logger.debug(f"Previous close para {symbol}: {previous_close}")
                
                # Verificar se os valores estão corretos antes de calcular
                if previous_close is not None and previous_close > 0:
                    price_change = last_price - previous_close
                    price_change_percent = (price_change / previous_close * 100)
                    logger.debug(f"Cálculo no banco para {symbol}: last={last_price}, previous_close={previous_close}, change={price_change:.4f}, change_percent={price_change_percent:.4f}%")
                else:
                    logger.debug(f"Não foi possível calcular variação para {symbol}: previous_close={previous_close}")
                    # Tentar usar open_price como fallback apenas para debugging
                    if open_price > 0:
                        price_change = last_price - open_price
                        price_change_percent = (price_change / open_price * 100)
                        logger.debug(f"Fallback para debugging - {symbol}: last={last_price}, open_price={open_price}, change={price_change:.4f}, change_percent={price_change_percent:.4f}%")
                
                # O previous_close já foi obtido anteriormente, não precisamos obter novamente
                
                # Atualizar ou inserir os dados na tabela asset_metrics
                upsert_sql = text("""
                    INSERT INTO asset_metrics (
                        symbol, last_price, previous_close, previous_close_correct, price_change, price_change_percent, 
                        volume, open_price, high_price, low_price, updated_at
                    ) VALUES (
                        :symbol, :last_price, :previous_close, :previous_close, :price_change, :price_change_percent,
                        :volume, :open_price, :high_price, :low_price, NOW()
                    )
                    ON CONFLICT (symbol) 
                    DO UPDATE SET
                        last_price = EXCLUDED.last_price,
                        previous_close = COALESCE(EXCLUDED.previous_close, asset_metrics.previous_close),
                        previous_close_correct = COALESCE(EXCLUDED.previous_close_correct, asset_metrics.previous_close_correct),
                        price_change = EXCLUDED.price_change,
                        price_change_percent = EXCLUDED.price_change_percent,
                        volume = EXCLUDED.volume,
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        updated_at = NOW()
                """)
                
                logger.debug(f"Atualizando banco de dados para {symbol}: open_price={open_price}, previous_close={previous_close}, last_price={last_price}, price_change={price_change:.4f}, price_change_percent={price_change_percent:.4f}%")
                
                # Verificar se os valores estão corretos antes de atualizar
                logger.debug(f"Valores finais para {symbol}:")
                logger.debug(f"  last_price: {last_price}")
                logger.debug(f"  previous_close: {previous_close}")
                logger.debug(f"  open_price: {open_price}")
                logger.debug(f"  price_change: {price_change:.4f}")
                logger.debug(f"  price_change_percent: {price_change_percent:.4f}%")
                
                conn.execute(upsert_sql, {
                    "symbol": symbol,
                    "last_price": last_price,
                    "previous_close": previous_close,
                    "price_change": price_change,
                    "price_change_percent": price_change_percent,
                    "volume": float(quote.get("volume", 0)),
                    "open_price": open_price if open_price > 0 else None,
                    "high_price": float(quote.get("high_price", last_price)),
                    "low_price": float(quote.get("low_price", last_price))
                })
                
                conn.commit()
                logger.info(f"AssetMetrics atualizado com sucesso para {symbol}")
                
        except Exception as e:
            logger.error(f"Erro ao atualizar AssetMetrics para {quote.get('symbol', 'unknown')}: {e}")
            logger.error(f"Dados do quote: {quote}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def subscribe_ticker(self, room: str, ticker: str):
        """Subscreve um ticker e ativa tempo real imediatamente."""
        try:
            if room not in self.active_subscriptions:
                self.active_subscriptions[room] = set()
            
            ticker_upper = ticker.upper()
            self.active_subscriptions[room].add(ticker_upper)
            
            # Tentar ativar tempo real para este ticker IMEDIATAMENTE
            if ticker_upper in self.mt5_symbols and ticker_upper not in self.realtime_symbols:
                self._activate_realtime_for_symbol(ticker_upper)
            
            logger.info(f"Ticker {ticker} subscrito para room {room}")
            logger.debug(f"Active subscriptions: {self.active_subscriptions}")
        except Exception as e:
            logger.error(f"Erro ao subscrever ticker {ticker} para room {room}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def unsubscribe_ticker(self, room: str, ticker: str):
        """Remove subscrição de um ticker."""
        if room in self.active_subscriptions:
            self.active_subscriptions[room].discard(ticker.upper())
            if not self.active_subscriptions[room]:
                del self.active_subscriptions[room]
        
        logger.info(f"Ticker {ticker} removido do room {room}")
        logger.debug(f"Active subscriptions: {self.active_subscriptions}")

    def get_subscription_stats(self):
        """Retorna estatísticas das subscrições."""
        try:
            total_subscriptions = sum(len(tickers) for tickers in self.active_subscriptions.values())
            
            stats = {
                "status": "active" if self.running else "inactive",
                "mt5_connected": self.mt5_connected,
                "total_rooms": len(self.active_subscriptions),
                "total_subscriptions": total_subscriptions,
                "total_symbols": len(self.mt5_symbols),
                "realtime_symbols": len(self.realtime_symbols),
                "failed_symbols": len(self.failed_symbols),
                "active_rooms": list(self.active_subscriptions.keys()),
                "database_connected": self.db_engine is not None,
                "worker_running": self.running,
                "last_update": datetime.now().isoformat(),
                "realtime_active": list(self.realtime_symbols),
                "realtime_failed": list(self.failed_symbols),
                "subscribed_tickers": {room: list(tickers) for room, tickers in self.active_subscriptions.items()}
            }
            
            logger.debug(f"Subscription stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "error": str(e),
                "mt5_connected": self.mt5_connected,
                "worker_running": self.running
            }

    def start(self):
        """Inicia o worker RTD em uma thread separada."""
        if self.running:
            logger.warning("Worker já está rodando.")
            return True

        logger.info("Iniciando MetaTrader5 RTD Worker TEMPO REAL...")

        try:
            self.initialize_mt5()
        except RuntimeError as e:
            logger.critical(
                f"Falha na inicialização do MT5. O worker não será iniciado: {e}"
            )
            raise  

        self.running = True
        self.worker_thread = threading.Thread(target=self._price_update_loop, daemon=True)
        self.worker_thread.start()
        logger.info("MetaTrader5 RTD Worker TEMPO REAL iniciado com sucesso.")
        return True
    
    def stop(self):
        """Para o worker RTD e desliga a conexão com o MT5."""
        logger.info("Parando MetaTrader5 RTD Worker...")
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        if self.mt5_connected and MT5_AVAILABLE:
            # Remover market books ativos
            for symbol in self.realtime_symbols:
                try:
                    mt5.market_book_release(symbol)
                except:
                    pass
            
            mt5.shutdown()
            logger.info("Conexão com MetaTrader5 encerrada.")
        
        logger.info("MetaTrader5 RTD Worker parado.")

# --- Singleton Pattern para o Worker ---
rtd_worker_instance = None

def get_rtd_worker():
    """Retorna a instância única (singleton) do RTD Worker."""
    global rtd_worker_instance
    return rtd_worker_instance

def initialize_rtd_worker(socketio_instance):
    """Cria, inicia e retorna a instância única do RTD Worker."""
    global rtd_worker_instance
    if rtd_worker_instance is None:
        logger.info("Criando nova instância do RTD Worker TEMPO REAL.")
        rtd_worker_instance = MetaTrader5RTDWorker(socketio_instance)
        rtd_worker_instance.start()
    else:
        logger.info("Usando instância existente do RTD Worker.")
        
    return rtd_worker_instance
