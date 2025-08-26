import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Carregar variáveis de ambiente
load_dotenv()

from backend import create_app
from backend.models import Company
from backend.utils.analysis_framework import generate_analysis_framework

def test_generate_framework():
    app = create_app()
    with app.app_context():
        try:
            # Obter uma empresa de exemplo
            company = Company.query.first()
            if company:
                print(f"Gerando framework para: {company.company_name}")
                framework = generate_analysis_framework(company)
                print("Framework gerado:")
                print("-" * 50)
                print(framework)
                print("-" * 50)
            else:
                print("Nenhuma empresa encontrada no banco de dados")
                
        except Exception as e:
            print(f"Erro ao gerar framework: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_generate_framework()