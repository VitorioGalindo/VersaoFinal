#!/bin/bash

# Script para instalação local do sistema de scraping
echo "🇧🇷 Instalação do Sistema de Scraping Financeiro Brasileiro"
echo "============================================================"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.8+ primeiro."
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Criar ambiente virtual
echo "📦 Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
echo "📥 Instalando dependências..."
pip install requests beautifulsoup4 psycopg2-binary python-dotenv pytz trafilatura selenium selenium-stealth webdriver-manager schedule lxml

# Configurar arquivo .env
echo "⚙️ Configurando arquivo .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Arquivo .env criado. Configure suas variáveis de ambiente."
else
    echo "⚠️ Arquivo .env já existe."
fi

echo ""
echo "🎉 Instalação concluída!"
echo ""
echo "📝 Próximos passos:"
echo "1. Configure suas variáveis no arquivo .env:"
echo "   - DATABASE_URL (PostgreSQL)"
echo "   - TRADERS_CLUB_USERNAME (opcional)"
echo "   - TRADERS_CLUB_PASSWORD (opcional)"
echo ""
echo "2. Para rodar uma vez:"
echo "   python run_scraper.py --portal all"
echo ""
echo "3. Para rodar continuamente (24/7):"
echo "   python automated_scraper.py"
echo ""
echo "4. Para testar portais específicos:"
echo "   python run_scraper.py --portal bdm"
echo "   python run_scraper.py --portal neofeed"
echo ""