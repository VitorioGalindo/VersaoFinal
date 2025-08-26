#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script principal para executar o scraper expandido.
"""

import sys
import argparse
from smart_scraper_expanded import (
    run_all_scrapers,
    scrape_infomoney_deep,
    scrape_g1_deep,
    scrape_brazil_journal,
    scrape_valor_economico,
    scrape_exame,
    scrape_uol_economia,
    scrape_cnn_brasil,
    scrape_estadao_economia,
    scrape_money_times,
    scrape_bom_dia_mercado,
    scrape_neofeed,
    scrape_petronoticias,
    scrape_traders_club_mover,
    save_articles_to_db
)
import logging

def main():
    parser = argparse.ArgumentParser(description='Scraper de Notícias Financeiras')
    parser.add_argument('--portal', choices=[
        'all', 'infomoney', 'g1', 'brazil-journal', 'valor', 
        'exame', 'uol', 'cnn', 'estadao', 'money-times',
        'bdm', 'neofeed', 'petronoticias', 'traders-club'
    ], default='all', help='Portal específico para scraping')
    parser.add_argument('--categoria', type=str, help='Categoria específica do InfoMoney')
    parser.add_argument('--url', type=str, help='URL específica da categoria do InfoMoney')
    
    args = parser.parse_args()
    
    try:
        if args.portal == 'all':
            logging.info("Executando scraping de todos os portais...")
            articles = run_all_scrapers()
            
        elif args.portal == 'infomoney':
            if args.categoria and args.url:
                logging.info(f"Executando scraping do InfoMoney - {args.categoria}")
                articles = scrape_infomoney_deep(args.categoria, args.url)
                save_articles_to_db(articles)
            else:
                logging.info("Executando scraping do InfoMoney - categorias padrão")
                articles = []
                categories = [
                    ("Mercados", "https://www.infomoney.com.br/mercados/"),
                    ("Economia", "https://www.infomoney.com.br/economia/"),
                    ("Empresas", "https://www.infomoney.com.br/negocios/")
                ]
                for cat_name, cat_url in categories:
                    articles.extend(scrape_infomoney_deep(cat_name, cat_url))
                save_articles_to_db(articles)
                
        elif args.portal == 'g1':
            logging.info("Executando scraping do G1 Economia")
            articles = scrape_g1_deep()
            save_articles_to_db(articles)
            
        elif args.portal == 'brazil-journal':
            logging.info("Executando scraping do Brazil Journal")
            articles = scrape_brazil_journal()
            save_articles_to_db(articles)
            
        elif args.portal == 'valor':
            logging.info("Executando scraping do Valor Econômico")
            articles = scrape_valor_economico()
            save_articles_to_db(articles)
            
        elif args.portal == 'exame':
            logging.info("Executando scraping da Exame")
            articles = scrape_exame()
            save_articles_to_db(articles)
            
        elif args.portal == 'uol':
            logging.info("Executando scraping do UOL Economia")
            articles = scrape_uol_economia()
            save_articles_to_db(articles)
            
        elif args.portal == 'cnn':
            logging.info("Executando scraping da CNN Brasil")
            articles = scrape_cnn_brasil()
            save_articles_to_db(articles)
            
        elif args.portal == 'estadao':
            logging.info("Executando scraping do Estadão Economia")
            articles = scrape_estadao_economia()
            save_articles_to_db(articles)
            
        elif args.portal == 'money-times':
            logging.info("Executando scraping do Money Times")
            articles = scrape_money_times()
            save_articles_to_db(articles)
            
        elif args.portal == 'bdm':
            logging.info("Executando scraping do Bom Dia Mercado")
            articles = scrape_bom_dia_mercado()
            save_articles_to_db(articles)
            
        elif args.portal == 'neofeed':
            logging.info("Executando scraping do Neo Feed")
            articles = scrape_neofeed()
            save_articles_to_db(articles)
            
        elif args.portal == 'petronoticias':
            logging.info("Executando scraping do Petro Notícias")
            articles = scrape_petronoticias()
            save_articles_to_db(articles)
            
        elif args.portal == 'traders-club':
            logging.info("Executando scraping do Traders Club")
            articles = scrape_traders_club_mover()
            save_articles_to_db(articles)
        
        logging.info("Scraping finalizado com sucesso!")
        
    except KeyboardInterrupt:
        logging.info("Scraping interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Erro durante execução: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
