import os
import sys
from datetime import date
from backend.routes.portfolio_routes import calculate_portfolio_summary
from backend import create_app

def test_portfolio_calculation():
    app = create_app()
    with app.app_context():
        try:
            print("Calculating portfolio summary for portfolio 1...")
            summary = calculate_portfolio_summary(1)
            
            if summary:
                print("Portfolio summary calculated successfully:")
                print(f"  Patrimônio líquido: {summary['patrimonio_liquido']}")
                print(f"  Valor da cota: {summary['valor_cota']}")
                print(f"  Variação da cota: {summary['variacao_cota_pct']}")
                print(f"  Posição comprada: {summary['posicao_comprada_pct']}")
                print(f"  Posição vendida: {summary['posicao_vendida_pct']}")
                print(f"  Net long: {summary['net_long_pct']}")
                print(f"  Exposição total: {summary['exposicao_total_pct']}")
                print(f"  Number of holdings: {len(summary['holdings'])}")
            else:
                print("Failed to calculate portfolio summary")
        except Exception as e:
            print(f"Error calculating portfolio summary: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_portfolio_calculation()