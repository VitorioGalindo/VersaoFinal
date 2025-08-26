import requests
import json

def test_frontend_data():
    try:
        # Make a request to the portfolio summary endpoint
        response = requests.get('http://localhost:5001/api/portfolio/1/summary')
        
        if response.status_code == 200:
            data = response.json()
            print("API Response:")
            print(json.dumps(data, indent=2))
            
            # Extract the summary data
            summary = data.get('summary', {})
            print("\nSummary data for frontend:")
            print(f"  Patrimônio Líquido: {summary.get('patrimonio_liquido', 0)}")
            print(f"  Valor da Cota: {summary.get('valor_cota', 0)}")
            print(f"  Variação da Cota: {summary.get('variacao_cota_pct', 0)}")
            print(f"  Posição Comprada: {summary.get('posicao_comprada_pct', 0)}")
            print(f"  Posição Vendida: {summary.get('posicao_vendida_pct', 0)}")
            print(f"  Net Long: {summary.get('net_long_pct', 0)}")
            print(f"  Exposição Total: {summary.get('exposicao_total_pct', 0)}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error making request: {e}")

if __name__ == "__main__":
    test_frontend_data()