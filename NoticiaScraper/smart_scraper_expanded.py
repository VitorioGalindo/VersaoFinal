# smart_scraper_expanded.py
# -*- coding: utf-8 -*-

# --- IMPORTS ATUALIZADOS ---
import os
import re
import json
import requests
import psycopg2
import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urljoin
from datetime import datetime
import pytz
import time
import trafilatura

# --- IMPORTS DO SELENIUM ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- NOVO IMPORT PARA O MODO STEALTH ---
from selenium_stealth import stealth

# --- Configuração Inicial ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("smart_scraper.log"), logging.StreamHandler()]
)
load_dotenv()

# --- Módulo de Análise de Conteúdo ---

def extract_tickers(text):
    """
    Extrai tickers de ações brasileiras (formato XXXX3, XXXX4, XXXX11) de um texto.
    """
    if not text:
        return []
    pattern = r'\b[A-Z]{4}(?:3|4|5|6|11)\b'
    tickers = re.findall(pattern, text.upper())
    return sorted(list(set(tickers)))

# --- Configuração do WebDriver ---

def setup_chrome_driver():
    """
    Configura e retorna um driver Chrome/Chromium com stealth mode.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Configurar para usar Chromium
    options.binary_location = "/usr/bin/chromium"
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    stealth(driver, 
           languages=["pt-BR", "pt"], 
           vendor="Google Inc.", 
           platform="Win32", 
           webgl_vendor="Intel Inc.", 
           renderer="Intel Iris OpenGL Engine", 
           fix_hairline=True)
    
    return driver

# --- Módulo de Banco de Dados ---

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', os.getenv('DB_HOST')),
            database=os.getenv('PGDATABASE', os.getenv('DB_NAME')),
            user=os.getenv('PGUSER', os.getenv('DB_USER')),
            password=os.getenv('PGPASSWORD', os.getenv('DB_PASSWORD')),
            port=os.getenv('PGPORT', os.getenv('DB_PORT', '5432'))
        )
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Falha ao conectar ao banco de dados: {e}")
        return None

def save_articles_to_db(article_list):
    """
    Salva ou ATUALIZA uma lista de artigos no banco de dados.
    """
    if not article_list:
        logging.info("Nenhum artigo novo para salvar.")
        return

    conn = get_db_connection()
    if not conn: 
        return

    updated_count = 0
    inserted_count = 0
    
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO artigos_mercado (
                    titulo, link_url, portal, resumo, conteudo_completo, autor, 
                    data_publicacao, categoria, tickers_relacionados
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (link_url) DO UPDATE SET
                    titulo = EXCLUDED.titulo,
                    resumo = EXCLUDED.resumo,
                    conteudo_completo = EXCLUDED.conteudo_completo,
                    autor = EXCLUDED.autor,
                    data_publicacao = EXCLUDED.data_publicacao,
                    categoria = EXCLUDED.categoria,
                    tickers_relacionados = EXCLUDED.tickers_relacionados,
                    data_coleta = CURRENT_TIMESTAMP;
            """
            for article in article_list:
                try:
                    tickers_json = json.dumps(article.get('tickers')) if article.get('tickers') else None
                    
                    cur.execute(sql, (
                        article.get('titulo'), article.get('link'), article.get('portal'),
                        article.get('resumo'), article.get('conteudo'), article.get('autor'),
                        article.get('data_publicacao'), article.get('categoria'), tickers_json
                    ))
                    
                    if 'INSERT' in cur.statusmessage:
                        inserted_count += 1
                    elif 'UPDATE' in cur.statusmessage:
                        updated_count += 1

                except Exception as e:
                    logging.error(f"Erro ao inserir/atualizar artigo '{article.get('titulo')}': {e}")
        
        conn.commit()
        logging.info(f"Processo de salvamento finalizado. Inseridos: {inserted_count}, Atualizados: {updated_count}.")
        
    except Exception as e:
        logging.error(f"Erro durante operação no banco: {e}")
        conn.rollback()
    finally:
        conn.close()

# --- Scrapers Existentes (InfoMoney e G1) ---

def scrape_infomoney_deep(categoria_nome, categoria_url):
    """
    Scraper do InfoMoney usando requests + BeautifulSoup + trafilatura como fallback.
    """
    logging.info(f"Iniciando scraping do InfoMoney para a seção: '{categoria_nome}'...")
    base_url = "https://www.infomoney.com.br"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        logging.info(f"Acessando a página da seção: '{categoria_url}'...")
        response = requests.get(categoria_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar links de artigos
        article_urls = set()
        
        # Procurar por diferentes seletores de artigos do InfoMoney
        selectors = [
            'main a[href]',
            'article a[href]',
            '.im-article-item a[href]',
            '.im-card a[href]',
            'h2 a[href]',
            'h3 a[href]'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and '/' in href:
                    full_url = urljoin(base_url, href)
                    # Filtrar apenas URLs de artigos válidos do InfoMoney
                    if ('infomoney.com.br' in full_url and 
                        href.count('/') >= 4 and 
                        not any(x in href for x in ['/tag/', '/autor/', '/page/', '/tudo-sobre/', '/categoria/'])):
                        article_urls.add(full_url)

        if not article_urls:
            logging.warning(f"Nenhum link de artigo encontrado para a seção '{categoria_nome}'.")
            return []

        logging.info(f"Encontrados {len(article_urls)} links únicos para a seção '{categoria_nome}'.")

        # Processar cada artigo
        for article_url in list(article_urls)[:10]:  # Limitar a 10 artigos
            logging.info(f"Processando artigo InfoMoney: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                titulo, resumo, data_publicacao, autor, conteudo, categoria_final = None, None, None, None, '', categoria_nome
                
                # Tentar extrair dados estruturados primeiro
                json_ld_script = article_soup.find('script', type='application/ld+json')
                if json_ld_script:
                    try:
                        data = json.loads(json_ld_script.string)
                        # Lidar com estruturas diferentes
                        if isinstance(data, list):
                            data = data[0] if data else {}
                        if isinstance(data, dict) and '@graph' in data:
                            graph = data.get('@graph', [])
                            article_node = next((node for node in graph if isinstance(node, dict) and node.get('@type') in ['Article', 'NewsArticle']), None)
                            if article_node:
                                titulo = article_node.get('headline')
                                resumo = article_node.get('description')
                                data_str = article_node.get('datePublished')
                                if data_str: 
                                    data_publicacao = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                                if article_node.get('author'): 
                                    if isinstance(article_node['author'], dict):
                                        autor = article_node['author'].get('name')
                                    elif isinstance(article_node['author'], list) and article_node['author']:
                                        autor = article_node['author'][0].get('name', '')
                    except Exception as e:
                        logging.debug(f"Erro ao processar JSON-LD: {e}")

                # Fallbacks para título
                if not titulo:
                    title_selectors = ['h1.im-title', 'h1', '.article-title', '.entry-title']
                    for selector in title_selectors:
                        title_tag = article_soup.select_one(selector)
                        if title_tag: 
                            titulo = title_tag.get_text(strip=True)
                            break
                
                # Extrair conteúdo
                content_selectors = ['.im-article', '.article-content', '.entry-content', 'article']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura se não encontrou conteúdo
                if not conteudo:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or ''
                    except:
                        pass
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))

                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo, 'link': article_url, 'portal': 'InfoMoney',
                        'resumo': resumo, 'conteudo': conteudo, 'autor': autor,
                        'data_publicacao': data_publicacao, 'categoria': categoria_final, 'tickers': tickers
                    })
                    logging.info(f"InfoMoney: Artigo '{str(titulo)[:40]}...' da seção '{categoria_nome}' processado.")
                else:
                    logging.warning(f"InfoMoney: Artigo em {article_url} pulado por falta de título.")

            except Exception as e:
                logging.error(f"Erro ao processar artigo InfoMoney {article_url}: {e}")
                continue

    except Exception as e:
        logging.error(f"Erro durante scraping da seção '{categoria_nome}' do InfoMoney: {e}")
    
    return enriched_articles

def scrape_g1_deep():
    """
    Raspa o portal g1 Economia com seletores atualizados.
    """
    logging.info("Iniciando scraping profundo do g1 Economia...")
    base_url = "https://g1.globo.com"
    url = f"{base_url}/economia/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    enriched_articles = []

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        article_links = soup.find_all('a', class_='feed-post-link', limit=15)
        if not article_links:
            logging.warning("Nenhum link de artigo encontrado no g1 Economia.")
            return []

        logging.info(f"g1 Economia: Encontrados {len(article_links)} links para processar.")

        for link_tag in article_links:
            article_url = urljoin(base_url, link_tag['href'])
            logging.info(f"Processando artigo g1: {article_url}")

            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article_response.content, 'html.parser')

                titulo_tag = article_soup.find('h1', class_='content-head__title')
                titulo = titulo_tag.get_text(strip=True) if titulo_tag else 'Título não encontrado'

                resumo_tag = article_soup.find('h2', class_='content-head__subtitle')
                resumo = resumo_tag.get_text(strip=True) if resumo_tag else ''

                data_tag = article_soup.find('time')
                data_publicacao = None
                if data_tag and data_tag.get('datetime'):
                    try:
                        data_publicacao = datetime.fromisoformat(data_tag['datetime'].replace('Z', '+00:00'))
                    except:
                        pass

                autor_tag = article_soup.find('p', class_='content-publication-data__from')
                autor = autor_tag.get_text(strip=True) if autor_tag else ''

                content_div = article_soup.find('div', class_='mc-article-content')
                conteudo = ''
                if content_div:
                    paragraphs = content_div.find_all('p', class_='content-text__container')
                    conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs)

                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))

                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo, 'link': article_url, 'portal': 'G1',
                        'resumo': resumo, 'conteudo': conteudo, 'autor': autor,
                        'data_publicacao': data_publicacao, 'categoria': 'Economia', 'tickers': tickers
                    })

            except Exception as e:
                logging.error(f"Erro ao processar artigo g1 {article_url}: {e}")

    except Exception as e:
        logging.error(f"Erro no scraping do g1: {e}")

    return enriched_articles

# --- Novos Scrapers: Brazil Journal e Valor Econômico ---

def scrape_brazil_journal():
    """
    Scraper para o Brazil Journal usando requests + BeautifulSoup + trafilatura.
    """
    logging.info("Iniciando scraping do Brazil Journal...")
    base_url = "https://braziljournal.com"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        # Acessar página principal
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar links de artigos
        article_links = set()
        
        # Tentar diferentes seletores para artigos do Brazil Journal
        selectors = [
            'a[href*="/artigos/"]',
            'a[href*="/economia/"]', 
            'a[href*="/mercados/"]',
            'a[href*="/negocios/"]',
            'article a',
            '.post-title a',
            '.entry-title a',
            '.card-title a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    # Filtrar apenas URLs de artigos válidos
                    if ('braziljournal.com' in full_url and 
                        len(href.split('/')) >= 4 and
                        not any(x in href for x in ['/tag/', '/autor/', '/categoria/', '/busca/'])):
                        article_links.add(full_url)
        
        if not article_links:
            logging.warning("Nenhum link encontrado no Brazil Journal.")
            return []
        
        logging.info(f"Brazil Journal: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:12]:  # Limitar a 12 artigos
            logging.info(f"Processando Brazil Journal: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['h1.entry-title', 'h1.post-title', 'h1', '.article-title', '.content-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.article-subtitle', '.entry-subtitle', 'h2.subtitle', '.post-excerpt']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.published-date', '.entry-date', '.post-date', '.date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.author-name', '.entry-author', '.by-author', '.post-author', '.author']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True)
                        break
                
                # Extrair conteúdo
                conteudo = ''
                content_selectors = ['.entry-content', '.article-content', '.post-content', 'article .content', '.content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura se não encontrou conteúdo
                if not conteudo:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or ''
                    except:
                        pass
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'Brazil Journal',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': 'Economia',
                        'tickers': tickers
                    })
                    logging.info(f"Brazil Journal: Artigo '{titulo[:40]}...' processado.")
                else:
                    logging.warning(f"Brazil Journal: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo Brazil Journal {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping do Brazil Journal: {e}")
    
    return enriched_articles

def scrape_valor_economico():
    """
    Scraper para o Valor Econômico usando requests + BeautifulSoup.
    """
    logging.info("Iniciando scraping do Valor Econômico...")
    base_url = "https://valor.globo.com"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        # Acessar página principal
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar links de artigos
        article_links = set()
        
        # Seletores para o Valor Econômico
        selectors = [
            'a[href*="/empresas/"]',
            'a[href*="/financas/"]',
            'a[href*="/brasil/"]',
            'a[href*="/mundo/"]',
            '.feed-post-link',
            '.manchete a',
            'article a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    # Filtrar apenas URLs de artigos válidos
                    if ('valor.globo.com' in full_url and 
                        len(href.split('/')) >= 4 and
                        not any(x in href for x in ['/tag/', '/autor/', '/busca/', '/tudo-sobre/'])):
                        article_links.add(full_url)
        
        if not article_links:
            logging.warning("Nenhum link encontrado no Valor Econômico.")
            return []
        
        logging.info(f"Valor Econômico: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:15]:  # Limitar a 15 artigos
            logging.info(f"Processando Valor Econômico: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['.content-head__title', 'h1.entry-title', 'h1', '.article-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.content-head__subtitle', '.article-subtitle', '.entry-subtitle']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.content-publication-data__updated', '.published-date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.content-publication-data__from', '.entry-author', '.author-name']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True)
                        break
                
                # Extrair conteúdo
                conteudo = ''
                content_selectors = ['.mc-article-content', '.entry-content', '.article-content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura se não encontrou conteúdo
                if not conteudo:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or ''
                    except:
                        pass
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                # Determinar categoria baseada na URL
                categoria = 'Economia'
                if '/empresas/' in article_url:
                    categoria = 'Empresas'
                elif '/financas/' in article_url:
                    categoria = 'Finanças'
                elif '/brasil/' in article_url:
                    categoria = 'Brasil'
                elif '/mundo/' in article_url:
                    categoria = 'Mundo'
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'Valor Econômico',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': categoria,
                        'tickers': tickers
                    })
                    logging.info(f"Valor Econômico: Artigo '{titulo[:40]}...' processado.")
                else:
                    logging.warning(f"Valor Econômico: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo Valor Econômico {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping do Valor Econômico: {e}")
    
    return enriched_articles

# --- Novos Scrapers: Portais Adicionais Solicitados ---

def scrape_bom_dia_mercado():
    """
    Scraper para o Bom Dia Mercado - incluindo BDM Express e Morning Call.
    """
    logging.info("Iniciando scraping do Bom Dia Mercado...")
    base_url = "https://www.bomdiamercado.com.br"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        # Acessar página principal
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_links = set()
        
        # Seletores para BDM - incluindo áreas premium que podem estar acessíveis
        selectors = [
            'a[href*="/morning-call/"]',
            'a[href*="/bdm-express/"]',
            'a[href*="/noticias/"]',
            'a[href*="/analises/"]',
            'a[href*="/mercados/"]',
            '.post-title a',
            '.entry-title a',
            'article a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if ('bomdiamercado.com.br' in full_url and 
                        len(href.split('/')) >= 3 and
                        not any(x in href for x in ['/tag/', '/autor/', '/categoria/', '/busca/'])):
                        article_links.add(full_url)
        
        # Tentar acessar URLs específicas que podem estar disponíveis
        premium_urls = [
            f"{base_url}/morning-call/",
            f"{base_url}/bdm-express/",
            f"{base_url}/analises/",
            f"{base_url}/mercados/"
        ]
        
        for premium_url in premium_urls:
            try:
                premium_response = requests.get(premium_url, headers=headers, timeout=10)
                if premium_response.status_code == 200:
                    premium_soup = BeautifulSoup(premium_response.content, 'html.parser')
                    
                    for selector in selectors:
                        links = premium_soup.select(selector)
                        for link in links:
                            href = link.get('href')
                            if href:
                                full_url = urljoin(base_url, href)
                                if 'bomdiamercado.com.br' in full_url:
                                    article_links.add(full_url)
                                    
            except Exception as e:
                logging.warning(f"Acesso premium falhou para {premium_url}: {e}")
                continue
        
        if not article_links:
            logging.warning("Nenhum link encontrado no Bom Dia Mercado.")
            return []
        
        logging.info(f"Bom Dia Mercado: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:15]:
            logging.info(f"Processando BDM: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = [
                    'h1.entry-title', 'h1.post-title', 'h1', '.article-title', 
                    '.content-title', '.morning-call-title', '.bdm-title'
                ]
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo/subtítulo
                resumo = None
                subtitle_selectors = [
                    '.article-subtitle', '.entry-subtitle', '.post-excerpt', 
                    '.excerpt', '.lead', '.summary', '.morning-call-summary'
                ]
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data com múltiplos formatos
                data_publicacao = None
                date_selectors = [
                    'time[datetime]', '.published-date', '.entry-date', 
                    '.post-date', '.date', '.article-date', '.bdm-date'
                ]
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            # Múltiplos formatos de data
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            elif '/' in date_str:
                                # Formato brasileiro dd/mm/yyyy
                                data_publicacao = datetime.strptime(date_str[:10], '%d/%m/%Y')
                            break
                        except:
                            continue
                
                # Extrair autor com melhor precisão
                autor = None
                author_selectors = [
                    '.author-name', '.entry-author', '.by-author', '.post-author', 
                    '.author', '.byline', '.writer', '.correspondent'
                ]
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True)
                        # Limpar texto comum de autor
                        autor = autor.replace('Por ', '').replace('por ', '').strip()
                        break
                
                # Extrair conteúdo completo com melhor seleção
                conteudo = ''
                content_selectors = [
                    '.entry-content', '.article-content', '.post-content', 
                    '.content', '.morning-call-content', '.bdm-content',
                    'article .text', '.main-content'
                ]
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        # Remover elementos indesejados
                        for unwanted in content_div.find_all(['script', 'style', 'nav', 'aside', 'footer']):
                            unwanted.decompose()
                        
                        paragraphs = content_div.find_all(['p', 'div', 'span'])
                        text_parts = []
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if text and len(text) > 20:  # Filtrar textos muito curtos
                                text_parts.append(text)
                        conteudo = ' '.join(text_parts)
                        break
                
                # Fallback com trafilatura para conteúdo mais limpo
                if not conteudo or len(conteudo) < 100:
                    try:
                        extracted_text = trafilatura.extract(article_response.text)
                        if extracted_text and len(extracted_text) > len(conteudo):
                            conteudo = extracted_text
                    except:
                        pass
                
                # Determinar categoria baseada na URL e conteúdo
                categoria = 'Mercados'
                if '/morning-call/' in article_url:
                    categoria = 'Morning Call'
                elif '/bdm-express/' in article_url:
                    categoria = 'BDM Express'
                elif '/analises/' in article_url:
                    categoria = 'Análises'
                elif '/noticias/' in article_url:
                    categoria = 'Notícias'
                
                # Extrair tickers com contexto melhorado
                full_text = f"{titulo or ''} {resumo or ''} {conteudo or ''}"
                tickers = extract_tickers(full_text)
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'Bom Dia Mercado',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': categoria,
                        'tickers': tickers
                    })
                    logging.info(f"BDM: Artigo '{titulo[:40]}...' processado ({categoria}).")
                else:
                    logging.warning(f"BDM: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo BDM {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping do Bom Dia Mercado: {e}")
    
    return enriched_articles

def scrape_neofeed():
    """
    Scraper para o Neo Feed - abas principal, negócios e economia.
    """
    logging.info("Iniciando scraping do Neo Feed...")
    base_url = "https://neofeed.com.br"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        # Seções específicas do Neo Feed
        sections = [
            (base_url, "Principal"),
            (f"{base_url}/categoria/negocios/", "Negócios"),
            (f"{base_url}/categoria/economia/", "Economia")
        ]
        
        article_links = set()
        
        for section_url, section_name in sections:
            try:
                logging.info(f"Acessando seção {section_name}: {section_url}")
                response = requests.get(section_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Seletores para Neo Feed
                selectors = [
                    'a[href*="/categoria/negocios/"]',
                    'a[href*="/categoria/economia/"]',
                    'a[href*="/noticias/"]',
                    'article a',
                    '.post-title a',
                    '.entry-title a',
                    'h2 a',
                    'h3 a',
                    '.news-item a'
                ]
                
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(base_url, href)
                            if ('neofeed.com.br' in full_url and 
                                len(href.split('/')) >= 3 and
                                not any(x in href for x in ['/tag/', '/autor/', '/busca/', '/categoria/page/'])):
                                article_links.add((full_url, section_name))
                
                time.sleep(2)  # Delay entre seções
                
            except Exception as e:
                logging.error(f"Erro ao acessar seção Neo Feed {section_name}: {e}")
                continue
        
        if not article_links:
            logging.warning("Nenhum link encontrado no Neo Feed.")
            return []
        
        logging.info(f"Neo Feed: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url, source_section in list(article_links)[:15]:
            logging.info(f"Processando Neo Feed: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['h1.entry-title', 'h1.post-title', 'h1', '.article-title', '.news-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.article-subtitle', '.entry-subtitle', '.post-excerpt', '.excerpt', '.lead']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.published-date', '.entry-date', '.post-date', '.date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.author-name', '.entry-author', '.by-author', '.post-author', '.author']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True).replace('Por ', '').strip()
                        break
                
                # Extrair conteúdo completo
                conteudo = ''
                content_selectors = ['.entry-content', '.article-content', '.post-content', '.content', '.news-content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        for unwanted in content_div.find_all(['script', 'style', 'nav', 'aside']):
                            unwanted.decompose()
                        
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura
                if not conteudo or len(conteudo) < 100:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or conteudo
                    except:
                        pass
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'Neo Feed',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': source_section,
                        'tickers': tickers
                    })
                    logging.info(f"Neo Feed: Artigo '{titulo[:40]}...' processado ({source_section}).")
                else:
                    logging.warning(f"Neo Feed: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo Neo Feed {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping do Neo Feed: {e}")
    
    return enriched_articles

def scrape_petronoticias():
    """
    Scraper para o Petro Notícias - principais notícias.
    """
    logging.info("Iniciando scraping do Petro Notícias...")
    base_url = "https://petronoticias.com.br"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_links = set()
        
        # Seletores para Petro Notícias
        selectors = [
            'a[href*="/noticias/"]',
            'a[href*="/petroleo/"]',
            'a[href*="/gas/"]',
            'a[href*="/energia/"]',
            'article a',
            '.post-title a',
            '.entry-title a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if ('petronoticias.com.br' in full_url and 
                        len(href.split('/')) >= 3 and
                        not any(x in href for x in ['/tag/', '/autor/', '/categoria/', '/busca/'])):
                        article_links.add(full_url)
        
        if not article_links:
            logging.warning("Nenhum link encontrado no Petro Notícias.")
            return []
        
        logging.info(f"Petro Notícias: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:12]:
            logging.info(f"Processando Petro Notícias: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['h1.entry-title', 'h1.post-title', 'h1', '.article-title', '.news-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.article-subtitle', '.entry-subtitle', '.post-excerpt', '.excerpt']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.published-date', '.entry-date', '.post-date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.author-name', '.entry-author', '.by-author', '.post-author']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True).replace('Por ', '').strip()
                        break
                
                # Extrair conteúdo
                conteudo = ''
                content_selectors = ['.entry-content', '.article-content', '.post-content', '.content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        for unwanted in content_div.find_all(['script', 'style', 'nav']):
                            unwanted.decompose()
                        
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura
                if not conteudo or len(conteudo) < 100:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or conteudo
                    except:
                        pass
                
                # Determinar categoria
                categoria = 'Energia'
                if '/petroleo/' in article_url:
                    categoria = 'Petróleo'
                elif '/gas/' in article_url:
                    categoria = 'Gás'
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'Petro Notícias',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': categoria,
                        'tickers': tickers
                    })
                    logging.info(f"Petro Notícias: Artigo '{titulo[:40]}...' processado.")
                else:
                    logging.warning(f"Petro Notícias: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo Petro Notícias {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping do Petro Notícias: {e}")
    
    return enriched_articles

def scrape_traders_club_mover(username=None, password=None):
    """
    Scraper para o Traders Club - seção Mover (requer login).
    """
    logging.info("Iniciando scraping do Traders Club - Mover...")
    
    # Usar credenciais das variáveis de ambiente se não fornecidas
    if not username:
        username = os.getenv('TRADERS_CLUB_USERNAME')
    if not password:
        password = os.getenv('TRADERS_CLUB_PASSWORD')
    
    # Verificar se as credenciais foram fornecidas
    if not username or not password:
        logging.warning("Credenciais do Traders Club não encontradas. Tentando acesso sem login...")
    else:
        logging.info("Credenciais do Traders Club encontradas. Realizando login...")
    
    base_url = "https://tc.tradersclub.com.br/mover"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        
        # Tentar fazer login se credenciais foram fornecidas
        if username and password:
            try:
                # Primeiro, acessar a página principal para pegar cookies
                main_page = session.get("https://tc.tradersclub.com.br", timeout=15)
                
                # Tentar diferentes URLs de login
                login_urls = [
                    "https://tc.tradersclub.com.br/login",
                    "https://tc.tradersclub.com.br/auth/login",
                    "https://tradersclub.com.br/login"
                ]
                
                login_success = False
                
                for login_url in login_urls:
                    try:
                        logging.info(f"Tentando login em: {login_url}")
                        
                        # Obter página de login
                        login_page = session.get(login_url, timeout=15)
                        
                        if login_page.status_code != 200:
                            continue
                            
                        login_soup = BeautifulSoup(login_page.content, 'html.parser')
                        
                        # Procurar por diferentes tipos de tokens
                        csrf_token = None
                        
                        # Verificar diferentes nomes de token
                        token_names = ['_token', 'csrf_token', 'authenticity_token']
                        for token_name in token_names:
                            csrf_input = login_soup.find('input', {'name': token_name})
                            if csrf_input:
                                csrf_token = csrf_input.get('value')
                                break
                        
                        # Verificar meta tag csrf
                        if not csrf_token:
                            csrf_meta = login_soup.find('meta', {'name': 'csrf-token'})
                            if csrf_meta:
                                csrf_token = csrf_meta.get('content')
                        
                        # Dados de login com diferentes formatos
                        login_data_options = [
                            {'email': username, 'password': password},
                            {'username': username, 'password': password},
                            {'login': username, 'password': password}
                        ]
                        
                        for login_data in login_data_options:
                            if csrf_token:
                                login_data['_token'] = csrf_token
                            
                            # Fazer login
                            login_response = session.post(login_url, data=login_data, timeout=15, allow_redirects=True)
                            
                            # Verificar se o login foi bem-sucedido
                            if login_response.status_code == 200:
                                # Verificar se foi redirecionado ou se há indicadores de sucesso
                                response_text = login_response.text.lower()
                                
                                # Indicadores de login bem-sucedido
                                success_indicators = ['dashboard', 'mover', 'logout', 'sair', 'perfil']
                                error_indicators = ['erro', 'error', 'invalid', 'incorret', 'failed']
                                
                                has_success = any(indicator in response_text for indicator in success_indicators)
                                has_error = any(indicator in response_text for indicator in error_indicators)
                                
                                if has_success and not has_error:
                                    logging.info("Login no Traders Club realizado com sucesso.")
                                    login_success = True
                                    break
                            
                        if login_success:
                            break
                            
                    except Exception as e:
                        logging.warning(f"Erro ao tentar login em {login_url}: {e}")
                        continue
                
                if not login_success:
                    logging.warning("Falha no login do Traders Club. Continuando sem autenticação.")
                    
            except Exception as e:
                logging.error(f"Erro geral no processo de login: {e}")
                logging.warning("Continuando sem autenticação.")
        
        # Acessar página Mover
        response = session.get(base_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_links = set()
        
        # Seletores para Traders Club - Mover
        selectors = [
            'a[href*="/mover/"]',
            'a[href*="/noticias/"]',
            'a[href*="/analises/"]',
            'article a',
            '.post-title a',
            '.entry-title a',
            '.news-item a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin("https://tc.tradersclub.com.br", href)
                    if ('tradersclub.com.br' in full_url and 
                        len(href.split('/')) >= 2 and
                        not any(x in href for x in ['/login', '/register', '/profile'])):
                        article_links.add(full_url)
        
        if not article_links:
            logging.warning("Nenhum link encontrado no Traders Club - Mover.")
            return []
        
        logging.info(f"Traders Club: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:10]:
            logging.info(f"Processando Traders Club: {article_url}")
            
            try:
                article_response = session.get(article_url, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['h1.entry-title', 'h1.post-title', 'h1', '.article-title', '.news-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.article-subtitle', '.entry-subtitle', '.post-excerpt', '.excerpt']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.published-date', '.entry-date', '.post-date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.author-name', '.entry-author', '.by-author', '.post-author']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True).replace('Por ', '').strip()
                        break
                
                # Extrair conteúdo
                conteudo = ''
                content_selectors = ['.entry-content', '.article-content', '.post-content', '.content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        for unwanted in content_div.find_all(['script', 'style', 'nav']):
                            unwanted.decompose()
                        
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura
                if not conteudo or len(conteudo) < 100:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or conteudo
                    except:
                        pass
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'Traders Club',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': 'Mover',
                        'tickers': tickers
                    })
                    logging.info(f"Traders Club: Artigo '{titulo[:40]}...' processado.")
                else:
                    logging.warning(f"Traders Club: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo Traders Club {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping do Traders Club: {e}")
    
    return enriched_articles

# --- Novos Scrapers: Portais Adicionais ---

def scrape_exame():
    """
    Scraper para a revista Exame - seção economia/negócios.
    """
    logging.info("Iniciando scraping da Exame...")
    base_url = "https://exame.com"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        # Acessar seções principais da Exame
        sections = [
            f"{base_url}/economia/",
            f"{base_url}/negocios/",
            f"{base_url}/mercados/"
        ]
        
        article_links = set()
        
        for section_url in sections:
            try:
                response = requests.get(section_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Seletores para a Exame
                selectors = [
                    'a[href*="/economia/"]',
                    'a[href*="/negocios/"]', 
                    'a[href*="/mercados/"]',
                    'article a',
                    '.post-title a',
                    'h2 a',
                    'h3 a'
                ]
                
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(base_url, href)
                            if ('exame.com' in full_url and 
                                len(href.split('/')) >= 4 and
                                not any(x in href for x in ['/tag/', '/autor/', '/categoria/', '/busca/'])):
                                article_links.add(full_url)
                
                time.sleep(2)  # Delay entre seções
                
            except Exception as e:
                logging.error(f"Erro ao acessar seção Exame {section_url}: {e}")
                continue
        
        if not article_links:
            logging.warning("Nenhum link encontrado na Exame.")
            return []
        
        logging.info(f"Exame: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:12]:
            logging.info(f"Processando Exame: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['h1.entry-title', 'h1.post-title', 'h1', '.article-title', '.content-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.article-subtitle', '.entry-subtitle', '.post-excerpt', '.excerpt']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.published-date', '.entry-date', '.post-date', '.date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.author-name', '.entry-author', '.by-author', '.post-author', '.author']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True)
                        break
                
                # Extrair conteúdo
                conteudo = ''
                content_selectors = ['.entry-content', '.article-content', '.post-content', 'article .content', '.content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura
                if not conteudo:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or ''
                    except:
                        pass
                
                # Determinar categoria
                categoria = 'Economia'
                if '/negocios/' in article_url:
                    categoria = 'Negócios'
                elif '/mercados/' in article_url:
                    categoria = 'Mercados'
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'Exame',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': categoria,
                        'tickers': tickers
                    })
                    logging.info(f"Exame: Artigo '{titulo[:40]}...' processado.")
                else:
                    logging.warning(f"Exame: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo Exame {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping da Exame: {e}")
    
    return enriched_articles

def scrape_uol_economia():
    """
    Scraper para o UOL Economia.
    """
    logging.info("Iniciando scraping do UOL Economia...")
    base_url = "https://economia.uol.com.br"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_links = set()
        
        # Seletores para o UOL Economia
        selectors = [
            'a[href*="/economia/"]',
            'a[href*="/financas/"]',
            'a[href*="/mercados/"]',
            '.manchete a',
            'article a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if ('uol.com.br' in full_url and 
                        '/economia/' in full_url and
                        len(href.split('/')) >= 4 and
                        not any(x in href for x in ['/tag/', '/autor/', '/busca/', '/tudo-sobre/'])):
                        article_links.add(full_url)
        
        if not article_links:
            logging.warning("Nenhum link encontrado no UOL Economia.")
            return []
        
        logging.info(f"UOL Economia: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:12]:
            logging.info(f"Processando UOL Economia: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['.custom-title', 'h1.entry-title', 'h1', '.article-title', '.news-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.custom-subtitle', '.article-subtitle', '.entry-subtitle', '.excerpt']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.published-date', '.entry-date', '.news-date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.author-name', '.entry-author', '.by-author', '.news-author']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True)
                        break
                
                # Extrair conteúdo
                conteudo = ''
                content_selectors = ['.custom-content', '.entry-content', '.article-content', '.news-content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura
                if not conteudo:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or ''
                    except:
                        pass
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'UOL Economia',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': 'Economia',
                        'tickers': tickers
                    })
                    logging.info(f"UOL Economia: Artigo '{titulo[:40]}...' processado.")
                else:
                    logging.warning(f"UOL Economia: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo UOL Economia {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping do UOL Economia: {e}")
    
    return enriched_articles

def scrape_cnn_brasil():
    """
    Scraper para a CNN Brasil - seção business.
    """
    logging.info("Iniciando scraping da CNN Brasil...")
    base_url = "https://www.cnnbrasil.com.br"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        # Acessar seção business da CNN Brasil
        business_url = f"{base_url}/business/"
        response = requests.get(business_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_links = set()
        
        # Seletores para a CNN Brasil
        selectors = [
            'a[href*="/business/"]',
            'a[href*="/economia/"]',
            'article a',
            '.card-title a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if ('cnnbrasil.com.br' in full_url and 
                        ('/business/' in full_url or '/economia/' in full_url) and
                        len(href.split('/')) >= 4 and
                        not any(x in href for x in ['/tag/', '/autor/', '/busca/', '/categoria/'])):
                        article_links.add(full_url)
        
        if not article_links:
            logging.warning("Nenhum link encontrado na CNN Brasil.")
            return []
        
        logging.info(f"CNN Brasil: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:10]:
            logging.info(f"Processando CNN Brasil: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['h1.news-item-title', 'h1.entry-title', 'h1', '.article-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.news-item-subtitle', '.article-subtitle', '.entry-subtitle']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.news-item-date', '.published-date', '.entry-date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.news-item-author', '.author-name', '.entry-author', '.by-author']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True)
                        break
                
                # Extrair conteúdo
                conteudo = ''
                content_selectors = ['.news-item-content', '.entry-content', '.article-content', '.content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura
                if not conteudo:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or ''
                    except:
                        pass
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'CNN Brasil',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': 'Business',
                        'tickers': tickers
                    })
                    logging.info(f"CNN Brasil: Artigo '{titulo[:40]}...' processado.")
                else:
                    logging.warning(f"CNN Brasil: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo CNN Brasil {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping da CNN Brasil: {e}")
    
    return enriched_articles

def scrape_estadao_economia():
    """
    Scraper para o Estadão - seção economia.
    """
    logging.info("Iniciando scraping do Estadão Economia...")
    base_url = "https://economia.estadao.com.br"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_links = set()
        
        # Seletores para o Estadão
        selectors = [
            'a[href*="/economia/"]',
            'a[href*="/negocios/"]',
            'a[href*="/mercados/"]',
            'article a',
            '.manchete a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if ('estadao.com.br' in full_url and 
                        len(href.split('/')) >= 4 and
                        not any(x in href for x in ['/tag/', '/autor/', '/busca/', '/tudo-sobre/'])):
                        article_links.add(full_url)
        
        if not article_links:
            logging.warning("Nenhum link encontrado no Estadão Economia.")
            return []
        
        logging.info(f"Estadão Economia: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:10]:
            logging.info(f"Processando Estadão: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['h1.entry-title', 'h1', '.article-title', '.news-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.article-subtitle', '.entry-subtitle', '.excerpt']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.published-date', '.entry-date', '.date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.author-name', '.entry-author', '.by-author']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True)
                        break
                
                # Extrair conteúdo
                conteudo = ''
                content_selectors = ['.entry-content', '.article-content', '.news-content', '.content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura
                if not conteudo:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or ''
                    except:
                        pass
                
                # Determinar categoria
                categoria = 'Economia'
                if '/negocios/' in article_url:
                    categoria = 'Negócios'
                elif '/mercados/' in article_url:
                    categoria = 'Mercados'
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'Estadão',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': categoria,
                        'tickers': tickers
                    })
                    logging.info(f"Estadão: Artigo '{titulo[:40]}...' processado.")
                else:
                    logging.warning(f"Estadão: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo Estadão {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping do Estadão: {e}")
    
    return enriched_articles

def scrape_money_times():
    """
    Scraper para o Money Times.
    """
    logging.info("Iniciando scraping do Money Times...")
    base_url = "https://www.moneytimes.com.br"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    enriched_articles = []
    
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_links = set()
        
        # Seletores para o Money Times
        selectors = [
            'a[href*="/mercados/"]',
            'a[href*="/economia/"]',
            'a[href*="/negocios/"]',
            'a[href*="/financas/"]',
            'article a',
            '.post-title a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if ('moneytimes.com.br' in full_url and 
                        len(href.split('/')) >= 4 and
                        not any(x in href for x in ['/tag/', '/autor/', '/busca/', '/categoria/'])):
                        article_links.add(full_url)
        
        if not article_links:
            logging.warning("Nenhum link encontrado no Money Times.")
            return []
        
        logging.info(f"Money Times: Encontrados {len(article_links)} links únicos.")
        
        # Processar cada artigo
        for article_url in list(article_links)[:12]:
            logging.info(f"Processando Money Times: {article_url}")
            
            try:
                article_response = requests.get(article_url, headers=headers, timeout=10)
                article_response.raise_for_status()
                
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extrair título
                titulo = None
                title_selectors = ['h1.entry-title', 'h1.post-title', 'h1', '.article-title']
                for selector in title_selectors:
                    title_tag = article_soup.select_one(selector)
                    if title_tag:
                        titulo = title_tag.get_text(strip=True)
                        break
                
                # Extrair resumo
                resumo = None
                subtitle_selectors = ['.article-subtitle', '.entry-subtitle', '.post-excerpt']
                for selector in subtitle_selectors:
                    subtitle_tag = article_soup.select_one(selector)
                    if subtitle_tag:
                        resumo = subtitle_tag.get_text(strip=True)
                        break
                
                # Extrair data
                data_publicacao = None
                date_selectors = ['time[datetime]', '.published-date', '.entry-date', '.post-date']
                for selector in date_selectors:
                    date_tag = article_soup.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                        try:
                            if 'T' in date_str:
                                data_publicacao = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Extrair autor
                autor = None
                author_selectors = ['.author-name', '.entry-author', '.by-author', '.post-author']
                for selector in author_selectors:
                    author_tag = article_soup.select_one(selector)
                    if author_tag:
                        autor = author_tag.get_text(strip=True)
                        break
                
                # Extrair conteúdo
                conteudo = ''
                content_selectors = ['.entry-content', '.article-content', '.post-content', '.content']
                for selector in content_selectors:
                    content_div = article_soup.select_one(selector)
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        conteudo = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        break
                
                # Fallback com trafilatura
                if not conteudo:
                    try:
                        conteudo = trafilatura.extract(article_response.text) or ''
                    except:
                        pass
                
                # Determinar categoria
                categoria = 'Economia'
                if '/mercados/' in article_url:
                    categoria = 'Mercados'
                elif '/negocios/' in article_url:
                    categoria = 'Negócios'
                elif '/financas/' in article_url:
                    categoria = 'Finanças'
                
                # Extrair tickers
                tickers = extract_tickers((titulo or '') + ' ' + (conteudo or ''))
                
                if titulo and article_url:
                    enriched_articles.append({
                        'titulo': titulo,
                        'link': article_url,
                        'portal': 'Money Times',
                        'resumo': resumo,
                        'conteudo': conteudo,
                        'autor': autor,
                        'data_publicacao': data_publicacao,
                        'categoria': categoria,
                        'tickers': tickers
                    })
                    logging.info(f"Money Times: Artigo '{titulo[:40]}...' processado.")
                else:
                    logging.warning(f"Money Times: Artigo em {article_url} pulado por falta de título.")
                
            except Exception as e:
                logging.error(f"Erro ao processar artigo Money Times {article_url}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Erro no scraping do Money Times: {e}")
    
    return enriched_articles

# --- Função Principal para Executar Todos os Scrapers ---

def run_all_scrapers():
    """
    Executa todos os scrapers disponíveis (13+ portais brasileiros).
    """
    logging.info("=== INICIANDO SCRAPING DE TODOS OS PORTAIS ===")
    
    all_articles = []
    
    # Lista completa de scrapers disponíveis
    scrapers = [
        ("G1 Economia", scrape_g1_deep),
        ("Brazil Journal", scrape_brazil_journal),
        ("Valor Econômico", scrape_valor_economico),
        ("Exame", scrape_exame),
        ("UOL Economia", scrape_uol_economia),
        ("CNN Brasil", scrape_cnn_brasil),
        ("Estadão Economia", scrape_estadao_economia),
        ("Money Times", scrape_money_times),
        ("Bom Dia Mercado", scrape_bom_dia_mercado),
        ("Neo Feed", scrape_neofeed),
        ("Petro Notícias", scrape_petronoticias),
        ("Traders Club", lambda: scrape_traders_club_mover())
    ]
    
    # Executar cada scraper
    for portal_name, scraper_func in scrapers:
        try:
            logging.info(f"Iniciando scraping: {portal_name}")
            articles = scraper_func()
            all_articles.extend(articles)
            logging.info(f"{portal_name}: {len(articles)} artigos coletados")
            time.sleep(3)  # Delay entre portais
        except Exception as e:
            logging.error(f"Erro no scraping do {portal_name}: {e}")
    
    # InfoMoney com categorias específicas (quando funcionar)
    infomoney_categories = [
        ("Mercados", "https://www.infomoney.com.br/mercados/"),
        ("Economia", "https://www.infomoney.com.br/economia/"),
        ("Empresas", "https://www.infomoney.com.br/negocios/")
    ]
    
    for categoria_nome, categoria_url in infomoney_categories:
        try:
            articles = scrape_infomoney_deep(categoria_nome, categoria_url)
            all_articles.extend(articles)
            time.sleep(5)  # Delay entre categorias
        except Exception as e:
            logging.error(f"Erro no scraping do InfoMoney categoria {categoria_nome}: {e}")
    
    # Salvar todos os artigos no banco
    if all_articles:
        logging.info(f"Total de artigos coletados: {len(all_articles)}")
        save_articles_to_db(all_articles)
    else:
        logging.warning("Nenhum artigo foi coletado de nenhum portal.")
    
    logging.info("=== SCRAPING FINALIZADO ===")
    return all_articles

if __name__ == "__main__":
    run_all_scrapers()
