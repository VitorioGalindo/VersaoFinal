# backend/routes/financials_routes.py
from flask import Blueprint, jsonify, request
from backend.models import Company, CvmFinancialData, Ticker
from backend import db
import logging

logger = logging.getLogger(__name__)
financials_bp = Blueprint('financials_bp', __name__)


@financials_bp.route('/<string:ticker_symbol>', methods=['GET'])
def get_financials_summary_by_ticker(ticker_symbol):
    """Retorna um resumo financeiro simplificado para um ticker.

    A rota original utilizava o sufixo `/summary`. Para facilitar o
    consumo pelo frontend e pelos testes automatizados também
    aceitamos a forma abreviada `/api/financials/<ticker>`.
    """
    try:
        # --- CORREÇÃO PRINCIPAL AQUI ---
        # A busca agora é exata e case-insensitive, forçando o uppercase. É mais robusta.
        ticker_obj = db.session.query(Ticker).filter(Ticker.symbol == ticker_symbol.upper()).first()
        
        if not ticker_obj:
            return jsonify({"success": False, "message": f"Ticker {ticker_symbol} não encontrado"}), 404
        
        company = ticker_obj.company
        if not company:
            return jsonify({"success": False, "message": f"Empresa para o ticker {ticker_symbol} não encontrada"}), 404

        # Busca as contas mais relevantes (Receita, Lucro) do último período disponível
        revenue = db.session.query(CvmFinancialData).filter(
            CvmFinancialData.company_id == company.id,
            CvmFinancialData.account_code == '3.01'
        ).order_by(CvmFinancialData.reference_date.desc()).first()

        net_income = db.session.query(CvmFinancialData).filter(
            CvmFinancialData.company_id == company.id,
            CvmFinancialData.account_code == '3.11'
        ).order_by(CvmFinancialData.reference_date.desc()).first()

        if not revenue and not net_income:
            return jsonify({"success": True, "message": "Dados financeiros não encontrados."})

        data = {
            "revenue": float(revenue.account_value) if revenue else "N/D",
            "net_income": float(net_income.account_value) if net_income else "N/D",
            "period": revenue.reference_date.isoformat() if revenue else "N/D",
            "report_type": revenue.report_type if revenue else "N/D"
        }

        return jsonify({"success": True, "ticker": ticker_symbol.upper(), "company_name": company.company_name, "data": data})

    except Exception as e:
        logger.error(f"Erro detalhado em get_financials_summary_by_ticker: {e}")
        return jsonify({"success": False, "error": "Erro interno ao buscar resumo financeiro"}), 500


@financials_bp.route('/history/<string:ticker_symbol>', methods=['GET'])
def get_financial_history(ticker_symbol):
    """Retorna o histórico financeiro completo de um ticker."""
    try:
        ticker_obj = db.session.query(Ticker).filter(Ticker.symbol == ticker_symbol.upper()).first()

        if not ticker_obj or not ticker_obj.company:
            return jsonify({"success": False, "message": f"Ticker {ticker_symbol} não encontrado"}), 404

        report_type = request.args.get('report_type')
        query = db.session.query(CvmFinancialData).filter(
            CvmFinancialData.company_id == ticker_obj.company.id
        )
        if report_type:
            query = query.filter(CvmFinancialData.report_type == report_type)

        records = query.order_by(CvmFinancialData.reference_date.asc()).all()

        data = []
        for r in records:
            data.append({
                "account_code": r.account_code,
                "account_name": r.account_name,
                "reference_date": r.reference_date.isoformat() if r.reference_date else None,
                "report_type": r.report_type,
                "report_version": r.report_version,
                "cvm_version": r.cvm_version,
                "account_value": float(r.account_value) if r.account_value is not None else None,
                "currency": r.currency,
                "is_fixed": r.is_fixed,
            })

        return jsonify({"success": True, "ticker": ticker_symbol.upper(), "data": data})

    except Exception as e:
        logger.error(f"Erro detalhado em get_financial_history: {e}")
        return jsonify({"success": False, "error": "Erro interno ao buscar histórico financeiro"}), 500
