# backend/routes/tickers_routes.py
from flask import Blueprint, jsonify, request
from backend.models import Ticker, Company
from backend import db
from sqlalchemy import or_
import logging

logger = logging.getLogger(__name__)
tickers_bp = Blueprint('tickers_bp', __name__)


@tickers_bp.route('/search', methods=['GET'])
def search_tickers():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({"success": True, "results": [], "count": 0, "query": query})

    try:
        search_term = f"%{query.upper()}%"

        results = (
            db.session.query(Ticker)
            .outerjoin(Company)
            .filter(
                or_(
                    Ticker.symbol.ilike(search_term),
                    # CORREÇÃO: Usando Company.company_name na busca
                    Company.company_name.ilike(search_term),
                    # Permite que company_name seja nulo
                    Company.company_name.is_(None),
                )
            )
            .limit(15)
            .all()
        )

        # --- CORREÇÃO PRINCIPAL AQUI ---
        # A resposta agora usa t.company.company_name, que é o nome correto do atributo.
        tickers_data = [
            {
                'symbol': t.symbol,
                'company_name': t.company.company_name if t.company else None,
            }
            for t in results
        ]

        return jsonify({"success": True, "query": query, "results": tickers_data, "count": len(tickers_data)})

    except Exception as e:
        logger.error(f"Erro detalhado em search_tickers: {e}")
        return jsonify({"error": "Erro interno ao buscar tickers.", "details": str(e)}), 500

