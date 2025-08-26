import logging
from flask import Blueprint, jsonify
from backend.models import Portfolio
from backend.routes.portfolio_routes import calculate_portfolio_summary

logger = logging.getLogger(__name__)
portfolio_summary_bp = Blueprint("portfolio_summary_bp", __name__)

@portfolio_summary_bp.route("/<int:portfolio_id>/summary", methods=["GET"])
def get_portfolio_summary_data(portfolio_id: int):
    """Retorna apenas os dados do resumo de um portfólio."""
    try:
        logger.info(f"Iniciando obtenção dos dados do resumo do portfólio {portfolio_id}")
        
        # Calcular o resumo do portfólio
        summary = calculate_portfolio_summary(portfolio_id)
        
        if not summary:
            logger.info(f"Portfólio {portfolio_id} não encontrado")
            return jsonify({
                "success": False, 
                "error": "Portfólio não encontrado"
            }), 404
        
        # Extrair apenas os dados do resumo (sem as holdings)
        summary_data = {
            "id": summary["id"],
            "name": summary["name"],
            "patrimonio_liquido": summary["patrimonio_liquido"],
            "valor_cota": summary["valor_cota"],
            "variacao_cota_pct": summary["variacao_cota_pct"],
            "posicao_comprada_pct": summary["posicao_comprada_pct"],
            "posicao_vendida_pct": summary["posicao_vendida_pct"],
            "net_long_pct": summary["net_long_pct"],
            "exposicao_total_pct": summary["exposicao_total_pct"],
        }
        
        logger.info(f"Retornando dados do resumo do portfólio {portfolio_id}")
        return jsonify({"success": True, "summary": summary_data})
    
    except Exception as e:
        logger.error(f"Erro em get_portfolio_summary_data para portfolio_id {portfolio_id}: {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return (
            jsonify({
                "success": False, 
                "error": "Erro interno ao buscar dados do resumo do portfólio", 
                "details": str(e)
            }),
            500,
        )