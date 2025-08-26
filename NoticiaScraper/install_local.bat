@echo off
echo 🇧🇷 Instalação do Sistema de Scraping Financeiro Brasileiro
echo ============================================================

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado. Instale Python 3.8+ primeiro.
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version

REM Criar ambiente virtual
echo 📦 Criando ambiente virtual...
python -m venv venv
call venv\Scripts\activate.bat

REM Instalar dependências
echo 📥 Instalando dependências...
pip install requests beautifulsoup4 psycopg2-binary python-dotenv pytz trafilatura selenium selenium-stealth webdriver-manager schedule lxml

REM Configurar arquivo .env
echo ⚙️ Configurando arquivo .env...
if not exist .env (
    copy .env.example .env
    echo ✅ Arquivo .env criado. Configure suas variáveis de ambiente.
) else (
    echo ⚠️ Arquivo .env já existe.
)

echo.
echo 🎉 Instalação concluída!
echo.
echo 📝 Próximos passos:
echo 1. Configure suas variáveis no arquivo .env:
echo    - DATABASE_URL (PostgreSQL)
echo    - TRADERS_CLUB_USERNAME (opcional)
echo    - TRADERS_CLUB_PASSWORD (opcional)
echo.
echo 2. Para rodar uma vez:
echo    python run_scraper.py --portal all
echo.
echo 3. Para rodar continuamente (24/7):
echo    python automated_scraper.py
echo.
echo 4. Para testar portais específicos:
echo    python run_scraper.py --portal bdm
echo    python run_scraper.py --portal neofeed
echo.
pause