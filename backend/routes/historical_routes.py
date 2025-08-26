from flask import Blueprint, jsonify, request
from backend.models import AssetMetrics
from backend import db
from datetime import datetime, timedelta

historical_bp = Blueprint('historical_bp', __name__)

@historical_bp.route('/<string:ticker>', methods=['GET'])
def get_historical_data(ticker):
    """
    Fornece dados históricos para um ticker.
    NOTA: Atualmente, esta rota retorna dados limitados da tabela de métricas.
    Para um histórico completo, um ETL para popular uma tabela de 'quotes' diários é necessário.
    """
    try:
        # Por enquanto, vamos retornar os dados mais recentes que temos na tabela de métricas.
        # Esta é uma simplificação. O ideal é ter uma tabela de histórico de preços.
        metric = db.session.query(AssetMetrics).filter(AssetMetrics.ticker.ilike(ticker)).first()

        if not metric:
            return jsonify({"success": False, "error": "Dados históricos não encontrados para o ticker."}), 404

        # Simula uma pequena série histórica para o gráfico com os dados que temos
        historical_data = [{
            "date": (metric.updated_at - timedelta(days=1)).strftime("%Y-%m-%d"),
            "open": metric.previous_close,
            "high": metric.previous_close,
            "low": metric.previous_close,
            "close": metric.previous_close,
            "volume": metric.volume * 0.8 if metric.volume else 0 # Simulação
        }, {
            "date": metric.updated_at.strftime("%Y-%m-%d"),
            "open": metric.open,
            "high": metric.high,
            "low": metric.low,
            "close": metric.last_price,
            "volume": metric.volume
        }]

        return jsonify({
            "success": True,
            "ticker": ticker.upper(),
            "data": historical_data,
        })

    except Exception as e:
        return jsonify({"success": False, "error": "Erro ao obter dados históricos.", "details": str(e)}), 500