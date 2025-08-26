
#!/usr/bin/env python3
"""
Script para executar o scraper financeiro localmente na pasta financial_scraper_package
"""
import os
import sys

# Adiciona o diretório atual ao Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configura as variáveis de ambiente
os.environ['DB_HOST'] = "localhost"
os.environ['DB_PORT'] = "5432"
os.environ['DB_NAME'] = "postgres3"
os.environ['DB_USER'] = "postgres"
os.environ['DB_PASSWORD'] = "Pandora337303$"

if __name__ == "__main__":
    print("🚀 Iniciando scraper financeiro...")
    print("📂 Executando da pasta financial_scraper_package")
    
    # Importa e executa o main
    from financials_realtime_user import main
    main()
