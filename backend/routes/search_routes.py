from flask import Blueprint, jsonify, request
from backend.models import Ticker, Company
from backend import db
from sqlalchemy import or_

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('/', methods=['GET'])
def global_search():
    """Realiza uma busca global por tickers e empresas."""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({"results": []})

    try:
        search_term = f"%{query.upper()}%"
        # Busca por ticker e nome da empresa usando os nomes corretos das colunas
        results = db.session.query(Ticker.symbol, Company.company_name).join(Company).filter(
            or_(
                Ticker.symbol.ilike(search_term),
                Company.company_name.ilike(search_term)
            )
        ).limit(10).all()

        formatted_results = [
            {"type": "ticker", "value": r[0], "label": f"{r[0]} - {r[1]}"}
            for r in results
        ]
        
        return jsonify({"results": formatted_results})
    except Exception as e:
        return jsonify({"error": "Erro interno na busca global"}), 500