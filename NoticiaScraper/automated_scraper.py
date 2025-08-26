#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema automatizado 24/7 para coleta contínua de notícias financeiras brasileiras.
Executa scraping periódico de todos os portais ativos.
"""

import schedule
import time
import logging
import sys
from datetime import datetime, timedelta
# NOVA IMPORTAÇÃO: Trazemos a função de conexão do outro script
from smart_scraper_expanded import run_all_scrapers, get_db_connection
import psycopg2
import os
from dotenv import load_dotenv

class AutomatedScraper:
    def __init__(self):
        self.setup_logging()
        self.last_success = None
        self.error_count = 0
        self.max_errors = 5
        
    def setup_logging(self):
        """Configura sistema de logging para operação 24/7."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('automated_scraper.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    def health_check(self):
        """Verifica se o sistema está saudável."""
        try:
            # MODIFICADO: Usa a função de conexão padronizada
            conn = get_db_connection()
            if not conn:
                raise ConnectionError("Falha ao obter conexão com o banco de dados.")

            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM artigos_mercado WHERE data_coleta > NOW() - INTERVAL '24 hours'")
            recent_count = cur.fetchone()[0]
            cur.close()
            conn.close()
            
            logging.info(f"Health Check: {recent_count} artigos coletados nas últimas 24h.")
            return True
            
        except Exception as e:
            logging.error(f"Health Check falhou: {e}")
            return False
    
    def run_scraping_cycle(self):
        """Executa um ciclo completo de scraping."""
        start_time = datetime.now()
        logging.info("=== INICIANDO CICLO DE SCRAPING AUTOMATIZADO ===")
        
        try:
            articles = run_all_scrapers()
            
            if articles and len(articles) > 0:
                self.last_success = datetime.now()
                self.error_count = 0
                
                duration = datetime.now() - start_time
                logging.info(f"CICLO BEM-SUCEDIDO: {len(articles)} artigos coletados em {duration}")
                
                self.log_quick_stats()
                
            else:
                self.error_count += 1
                logging.warning(f"AVISO: Nenhum artigo foi coletado neste ciclo (tentativa #{self.error_count})")
                
        except Exception as e:
            self.error_count += 1
            logging.error(f"ERRO no ciclo de scraping (tentativa #{self.error_count}): {e}")
            
        if self.error_count >= self.max_errors:
            logging.critical(f"ALERTA CRÍTICO: {self.error_count} ciclos de scraping consecutivos falharam!")
            
        logging.info("=== CICLO FINALIZADO ===\n")
    
    def log_quick_stats(self):
        """Mostra estatísticas rápidas do banco."""
        try:
            # MODIFICADO: Usa a função de conexão padronizada
            conn = get_db_connection()
            if not conn:
                raise ConnectionError("Falha ao obter conexão com o banco de dados para estatísticas.")

            cur = conn.cursor()
            
            cur.execute("""
                SELECT portal, COUNT(*) 
                FROM artigos_mercado 
                WHERE data_coleta > NOW() - INTERVAL '24 hours'
                GROUP BY portal 
                ORDER BY COUNT(*) DESC
            """)
            
            stats = cur.fetchall()
            if stats:
                logging.info("ESTATÍSTICAS (Últimas 24h): " + 
                           ", ".join([f"{portal}: {count}" for portal, count in stats]))
            
            cur.close()
            conn.close()
            
        except Exception as e:
            logging.warning(f"Erro ao obter estatísticas do banco: {e}")
    
    def run_continuous(self):
        """Executa o sistema continuamente."""
        logging.info("SISTEMA AUTOMATIZADO INICIADO")
        logging.info("Portais ativos: G1, Brazil Journal, Valor, Exame, Estadão, Money Times, BDM, Neo Feed, Petro Notícias")
        logging.info("Frequência: A cada 2 horas")
        logging.info("Health Check: A cada 30 minutos")
        
        schedule.every(2).hours.do(self.run_scraping_cycle)
        schedule.every(30).minutes.do(self.health_check)
        
        self.run_scraping_cycle()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
                
            except KeyboardInterrupt:
                logging.info("Sistema interrompido pelo usuário.")
                break
            except Exception as e:
                logging.error(f"Erro no loop principal do agendador: {e}")
                time.sleep(300)

def main():
    """Função principal."""
    load_dotenv()
    
    scraper = AutomatedScraper()
    
    # LÓGICA DE VERIFICAÇÃO ATUALIZADA
    # Verifica as variáveis individuais, assim como o get_db_connection faz.
    db_vars_std = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    db_vars_alt = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    
    has_std_creds = all(os.getenv(var) for var in db_vars_std)
    has_alt_creds = all(os.getenv(var) for var in db_vars_alt)

    if not has_std_creds and not has_alt_creds:
        logging.error("ERRO CRÍTICO: Nenhuma configuração de banco de dados encontrada. Verifique as variáveis (PG* ou DB_*) no arquivo .env!")
        sys.exit(1)
    
    try:
        scraper.run_continuous()
    except Exception as e:
        logging.critical(f"FALHA CRÍTICA no sistema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()