#!/usr/bin/env python3
import os
import sys
import time
import datetime
import subprocess
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

os.environ['DB_HOST'] = "localhost"
os.environ['DB_PORT'] = "5432"
os.environ['DB_NAME'] = "postgres3"
os.environ['DB_USER'] = "postgres"
os.environ['DB_PASSWORD'] = "Pandora337303$"

def ensure_playwright():
    try:
        import playwright
        print("✅ Playwright já está instalado.")
    except ImportError:
        print("📦 Playwright não encontrado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    print("🌐 Verificando e instalando browsers do Playwright (Chromium)...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"], check=True)
    print("✅ Browser Chromium configurado com sucesso!")

class Base(DeclarativeBase):
    pass

def create_database_url():
    host = os.environ.get('DB_HOST')
    user = os.environ.get('DB_USER') 
    password = os.environ.get('DB_PASSWORD')
    port = "5432"
    database = os.environ.get('DB_NAME')
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = create_database_url()
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 300, "pool_pre_ping": True}
db.init_app(app)

from models_user_custom import Company, CvmDocument

def main():
    ensure_playwright()
    with app.app_context():
        try:
            company_count = db.session.query(Company).count()
            financial_count = db.session.query(CvmDocument).count()
            print(f"✅ Conexão com o banco de dados estabelecida com sucesso!")
            print(f"📊 Empresas monitoradas: {company_count}")
            print(f"💰 Registros financeiros existentes: {financial_count:,}")
            if company_count == 0:
                print("❌ ERRO CRÍTICO: Nenhuma empresa encontrada no banco de dados.")
                return
        except Exception as e:
            print(f"❌ ERRO CRÍTICO: Falha ao conectar com o banco de dados: {e}")
            return
        
        from financials_scraper_user import FinancialsScraper
        scraper = FinancialsScraper(db)
        
        cycle_count = 0
        while True:
            cycle_count += 1
            print("-" * 70)
            print(f"⏰ CICLO #{cycle_count} | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            total_added_in_cycle = 0
            try:
                # 1. Executa a busca por ITR
                result_itr = scraper.run_check_itr()
                if result_itr.get('success'):
                    total_added_in_cycle += result_itr.get('new_documents', 0)
                
                print("\n-- Pausa de 10 segundos entre as buscas --\n")
                time.sleep(10) 

                # 2. Executa a busca por DFP
                result_dfp = scraper.run_check_dfp()
                if result_dfp.get('success'):
                    total_added_in_cycle += result_dfp.get('new_documents', 0)

                print(f"\n🏁 CICLO #{cycle_count} CONCLUÍDO. Total de {total_added_in_cycle} novos registros adicionados.")
                current_count = db.session.query(CvmDocument).count()
                print(f"📊 Total de registros financeiros no banco agora: {current_count:,}")
                    
            except Exception as e:
                print(f"❌ ERRO INESPERADO NO LOOP PRINCIPAL: {e}")
            
            interval_minutes = 30
            print(f"\n⏳ Aguardando {interval_minutes} minutos para a próxima verificação.")
            next_check = datetime.datetime.now() + datetime.timedelta(minutes=interval_minutes)
            print(f"🕐 Próxima execução agendada para: {next_check.strftime('%H:%M:%S')}")
            
            try:
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                print("\n🛑 Scraper interrompido pelo usuário. Finalizando...")
                break

if __name__ == "__main__":
    main()