from flask import Blueprint, jsonify
from backend.services.metatrader5_rtd_worker import get_rtd_worker
from backend.models import AssetMetrics
from backend import db
import logging
from datetime import datetime, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)
market_bp = Blueprint('market_bp', __name__)


@market_bp.route('/overview', methods=['GET'])
def get_market_overview():
    """Retorna um resumo simples do mercado baseado no banco de dados."""
    try:
        overview = {}

        index_map = {"IBOV": "ibovespa", "IFIX": "ifix", "USDBRL": "dolar"}
        for symbol, key in index_map.items():
            metric = db.session.get(AssetMetrics, symbol)
            if metric:
                overview[key] = {
                    "price": float(metric.last_price) if metric.last_price is not None else None,
                    "change_percent": float(metric.price_change_percent) if metric.price_change_percent is not None else None,
                }

        gainers = (
            db.session.query(AssetMetrics.symbol)
            .order_by(AssetMetrics.price_change_percent.desc())
            .limit(3)
            .all()
        )
        losers = (
            db.session.query(AssetMetrics.symbol)
            .order_by(AssetMetrics.price_change_percent.asc())
            .limit(3)
            .all()
        )
        overview["top_gainers"] = [g[0] for g in gainers]
        overview["top_losers"] = [l[0] for l in losers]

        return jsonify({"success": True, "data": overview})
    except Exception as e:
        logger.error(f"Erro em get_market_overview: {e}")
        return jsonify({"success": False, "error": "Erro ao obter overview do mercado"}), 500

@market_bp.route('/status', methods=['GET'])
def get_market_status():
    """Retorna o status geral do serviço de cotações e do worker MT5."""
    rtd_worker = get_rtd_worker()
    if not rtd_worker:
        return jsonify({"status": "inactive", "message": "RTD Worker não inicializado."}), 503
    return jsonify(rtd_worker.get_subscription_stats()), 200

@market_bp.route('/quotes/<string:ticker>', methods=['GET'])
@market_bp.route('/quote/<string:ticker>', methods=['GET'])
def get_quote(ticker):
    """Retorna a cotação em tempo real para um ticker específico."""
    rtd_worker = get_rtd_worker()
    if not rtd_worker or not rtd_worker.mt5_connected:
        return jsonify({"error": "Serviço de cotações (MT5) não disponível."}), 503

    ticker_upper = ticker.upper()
    quote = rtd_worker.get_mt5_quote(ticker_upper)

    if quote:
        return jsonify({"success": True, "ticker": ticker_upper, "quote": quote})
    else:
        return jsonify({"success": False, "error": f"Não foi possível obter a cotação para '{ticker_upper}'."}), 404


@market_bp.route('/ibov-history', methods=['GET'])
def get_ibov_history():
    """Retorna a série histórica do Ibovespa."""
    try:
        end = datetime.today().date()
        start = end - timedelta(days=365)
        data = yf.download('^BVSP', start=start, end=end, progress=False)[['Adj Close']]
        history = [
            {"date": idx.strftime('%Y-%m-%d'), "close": float(row['Adj Close'])}
            for idx, row in data.iterrows()
        ]
        return jsonify({"success": True, "history": history})
    except Exception as e:
        logger.error(f"Erro ao obter histórico do Ibovespa: {e}")
        return jsonify({"success": False, "error": "Erro ao obter histórico do Ibovespa"}), 500
