from flask import Blueprint, jsonify, request
from backend.models import Ticker, Company, AssetMetrics
from backend import db
import logging

logger = logging.getLogger(__name__)
screening_bp = Blueprint('screening_bp', __name__)


@screening_bp.route('/', methods=['GET', 'POST'])
def screen_stocks():
    """Realiza um screening de ações com base em filtros.

    - **GET** permite o envio de filtros via query string
    - **POST** aceita um JSON com os filtros
    """
    try:
        filters = request.get_json() if request.method == 'POST' else request.args.to_dict()

        query = (
            db.session.query(
                Ticker.symbol.label('ticker'),
                Company.company_name,
                AssetMetrics.sector,
                AssetMetrics.last_price
            )
            .join(Company)
            .outerjoin(AssetMetrics, AssetMetrics.symbol == Ticker.symbol)
        )

        sector = filters.get('sector') if filters else None
        if sector:
            query = query.filter(AssetMetrics.sector == sector)

        results = query.limit(50).all()
        formatted = [
            {
                'ticker': r.ticker,
                'company_name': r.company_name,
                'sector': r.sector,
                'price': float(r.last_price) if r.last_price is not None else None,
            }
            for r in results
        ]

        return jsonify({"success": True, "filters_applied": filters or {}, "results": formatted})
    except Exception as e:
        logger.error(f"Erro em screen_stocks: {e}")
        return jsonify({"success": False, "error": "Erro interno ao realizar screening"}), 500


@screening_bp.route('/sectors', methods=['GET'])
def get_screening_sectors():
    """Retorna a lista de setores disponíveis para o screening."""
    sectors = [
        s[0]
        for s in db.session.query(AssetMetrics.sector).distinct().order_by(AssetMetrics.sector).all()
        if s[0]
    ]
    return jsonify({"success": True, "sectors": sectors})