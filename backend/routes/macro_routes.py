from flask import Blueprint, jsonify, request
from backend import db
from sqlalchemy import text
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
macro_bp = Blueprint('macro_bp', __name__)


@macro_bp.route('/indicators', methods=['GET'])
def get_macro_indicators():
    """Retorna os indicadores macroeconômicos do Brasil a partir do banco de dados."""
    try:
        requested = [i.upper() for i in request.args.getlist('indicators')]
        result = db.session.execute(
            text("SELECT indicator, value, unit, description, updated_at FROM macro_indicators")
        )
        rows = result.fetchall() if hasattr(result, "fetchall") else result
        data = {}
        for row in rows:
            if not requested or row.indicator in requested:
                data[row.indicator] = {
                    "value": float(row.value) if row.value is not None else None,
                    "unit": row.unit,
                    "description": row.description,
                    "updated_at": row.updated_at.isoformat() if hasattr(row, 'updated_at') and row.updated_at else None,
                }

        if requested:
            missing = [ind for ind in requested if ind not in data]
            if missing:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Indicador(es) não encontrado(s)",
                            "missing": missing,
                        }
                    ),
                    404,
                )

        return jsonify({"success": True, "indicators": data})
    except Exception as e:
        logger.error(f"Erro em get_macro_indicators: {e}")
        return jsonify({"success": False, "error": "Indicadores não disponíveis"}), 500


@macro_bp.route('/historical/<string:indicator>', methods=['GET'])
def get_indicator_history(indicator):
    """Retorna dados históricos para um indicador."""
    indicator = indicator.upper()
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    start_date = end_date = None

    try:
        if start_str:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        if end_str:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return (
            jsonify({"success": False, "error": "Datas devem estar no formato YYYY-MM-DD"}),
            400,
        )

    if start_date and end_date and end_date < start_date:
        return (
            jsonify({"success": False, "error": "Data final deve ser posterior à inicial"}),
            400,
        )

    try:
        query = "SELECT date, value FROM macro_indicator_history WHERE indicator = :ind"
        params = {"ind": indicator}
        if start_date:
            query += " AND date >= :start"
            params["start"] = start_date
        if end_date:
            query += " AND date <= :end"
            params["end"] = end_date
        query += " ORDER BY date"

        rows = db.session.execute(text(query), params).fetchall()
        if not rows:
            return jsonify({"success": False, "error": "Indicador não encontrado"}), 404
        history = [
            {"date": r.date.isoformat(), "value": float(r.value) if r.value is not None else None}
            for r in rows
        ]
        return jsonify({"success": True, "indicator": indicator, "history": history})
    except Exception as e:
        logger.error(f"Erro em get_indicator_history: {e}")
        return jsonify({"success": False, "error": "Histórico não disponível"}), 500


@macro_bp.route('/summary', methods=['GET'])
def get_macro_summary():
    """Retorna um resumo geral dos indicadores."""
    try:
        rows = db.session.execute(
            text("SELECT indicator, value, unit FROM macro_indicators")
        )
        summary = {
            row.indicator: {
                "value": float(row.value) if row.value is not None else None,
                "unit": row.unit,
            }
            for row in rows
        }
        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        logger.error(f"Erro em get_macro_summary: {e}")
        return jsonify({"success": False, "error": "Resumo não disponível"}), 500


@macro_bp.route('/sync', methods=['POST'])
def sync_macro_data():
    """Dispara manualmente a sincronização dos indicadores macroeconômicos."""
    api_key = request.headers.get("X-API-KEY")
    expected_key = os.environ.get("SYNC_API_KEY")
    if not expected_key or api_key != expected_key:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        # Placeholder: inserir chamada real para o scraper aqui
        return jsonify({"success": True, "message": "Sincronização agendada"}), 202
    except Exception as e:
        logger.error(f"Erro em sync_macro_data: {e}")
        return jsonify({"success": False, "error": "Falha ao sincronizar"}), 500
