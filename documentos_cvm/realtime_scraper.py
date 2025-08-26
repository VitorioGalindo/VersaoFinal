# realtime_scraper.py (versão final com Playwright)
import os
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime
import re
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Importe os modelos e a função de salvar que já temos
from models import CvmDocument, Company
from scraper import save_to_db

# --- Configuração ---
load_dotenv()
CHECK_INTERVAL_SECONDS = 120  # 7 dias para o teste
CVM_URL = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"

# --- Conexão com o Banco ---
db_host = os.getenv("DB_HOST" )
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

if not all([db_host, db_port, db_name, db_user, db_password]):
    raise ValueError("ERRO CRÍTICO: Variáveis de ambiente do banco não definidas.")

DB_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def get_lookup_maps(session):
    print("Mapeando CNPJs e CVM_CODEs para IDs da tabela 'companies'...")
    companies = session.query(Company.id, Company.cnpj, Company.cvm_code).all()
    cnpj_map = {re.sub(r'[^\d]', '', company.cnpj): company.id for company in companies if company.cnpj}
    cvm_map = {company.cvm_code: company.id for company in companies if company.cvm_code}
    print(f"{len(cnpj_map)} empresas mapeadas por CNPJ.")
    print(f"{len(cvm_map)} empresas mapeadas por CVM_CODE.")
    return cnpj_map, cvm_map

def fetch_results_with_playwright():
    """
    Usa um navegador real (via Playwright) para preencher o formulário e obter o HTML dos resultados.
    """
    print("DEBUG: Iniciando navegador com Playwright para buscar os dados...")
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=7)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # headless=False para ver o navegador funcionando
        page = browser.new_page()
        
        try:
            print(f"DEBUG: Navegando para {CVM_URL}...")
            page.goto(CVM_URL, timeout=60000)
            
            print("DEBUG: Preenchendo o formulário...")
            # Clica no radio button "No período"
            page.locator('input#rdPeriodo').check()
            
            # Preenche as datas
            page.locator('input#txtDataIni').fill(start_date.strftime('%d/%m/%Y'))
            page.locator('input#txtDataFim').fill(end_date.strftime('%d/%m/%Y'))
            
            print("DEBUG: Clicando no botão 'Consultar'...")
            # Clica no botão de consulta e espera a página carregar
            page.locator('input#btnConsulta').click()
            
            # Espera a tabela de resultados aparecer. Este é um passo crucial.
            print("DEBUG: Aguardando a tabela de resultados carregar...")
            page.wait_for_selector('table#grdDocumentos', timeout=30000)
            
            print("DEBUG: Tabela de resultados carregada. Obtendo o HTML...")
            html_content = page.content()
            
            with open("debug_playwright_response.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("DEBUG: Resposta HTML do Playwright salva em 'debug_playwright_response.html'")
            
            return html_content

        except Exception as e:
            print(f"ERRO no Playwright: {e}")
            page.screenshot(path='playwright_error_screenshot.png')
            print("Screenshot do erro salvo em 'playwright_error_screenshot.png'")
            return None
        finally:
            browser.close()

# Em realtime_scraper.py, substitua apenas esta função

def parse_cvm_table(html_content, cnpj_map, cvm_code_map):
    """
    Analisa a tabela HTML usando uma lógica híbrida de CNPJ e CVM Code.
    Versão final com extração de texto robusta.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    documents = []
    table = soup.find('table', {'id': 'grdDocumentos'})
    if not table:
        print("DEBUG: A tabela com id 'grdDocumentos' NÃO foi encontrada no HTML recebido.")
        return []
    
    table_body = table.find('tbody')
    if not table_body:
        print("DEBUG: O corpo da tabela (tbody) NÃO foi encontrado.")
        return []

    rows = table_body.find_all('tr', recursive=False)
    if not rows:
        print("DEBUG: A tabela foi encontrada, mas está vazia (sem linhas <tr>).")
        return []

    print(f"DEBUG: Tabela encontrada com {len(rows)} linhas para processar.")
    
    i = 0
    docs_found_count = 0
    while i < len(rows):
        main_row = rows[i]
        if 'celulaAssunto' in main_row.get('class', []):
            i += 1
            continue
        if i + 1 >= len(rows) or 'celulaAssunto' not in rows[i+1].find('td').get('class', []):
            i += 1
            continue
            
        subject_row = rows[i+1]
        cols = main_row.find_all('td')
        if len(cols) < 11:
            i += 2
            continue

        try:
            identifier_raw = cols[0].text.strip()
            company_id = None

            if '/' in identifier_raw:
                cnpj_clean = re.sub(r'[^\d]', '', identifier_raw)
                company_id = cnpj_map.get(cnpj_clean)
            
            if not company_id:
                try:
                    cvm_code_num = int(re.sub(r'[^0-9-]', '', identifier_raw).replace('-', ''))
                    company_id = cvm_code_map.get(cvm_code_num)
                except (ValueError, TypeError):
                    pass

            if not company_id:
                i += 2
                continue

            # --- CORREÇÃO FINAL NA EXTRAÇÃO DE TEXTO ---
            # Usamos .find(text=True) para pegar apenas o texto visível da célula, ignorando tags filhas.
            categoria = cols[2].text.strip()
            tipo = cols[3].text.strip()
            especie = cols[4].find(text=True, recursive=False).strip()
            data_referencia_str = cols[5].find(text=True, recursive=False).strip()
            data_entrega_str = cols[6].find(text=True, recursive=False).strip()
            # --- FIM DA CORREÇÃO ---
            
            link_tag = cols[10].find('i', {'title': 'Download'})
            onclick_attr = link_tag['onclick']
            params = onclick_attr.split('(')[1].split(')')[0].split(',')
            protocolo = params[2].strip("'")
            # Alterado para usar o link de visualização em vez do link de download
            download_url = f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoIPEExterno.aspx?NumeroProtocoloEntrega={protocolo}"

            assunto_td = subject_row.find('td', class_='celulaAssunto' )
            assunto_completo = assunto_td.text.strip().replace('Assunto(s):', '').strip() if assunto_td else ""
            
            delivery_date = datetime.datetime.strptime(data_entrega_str, '%d/%m/%Y %H:%M')
            try:
                reference_date = datetime.datetime.strptime(data_referencia_str, '%d/%m/%Y')
            except (ValueError, TypeError):
                reference_date = delivery_date

            doc_data = {
                'company_id': company_id,
                'cvm_code': int(re.sub(r'[^0-9]', '', identifier_raw)),
                'document_type': tipo if tipo.strip() != '-' else None,
                'document_category': categoria,
                'title': assunto_completo if assunto_completo else (especie if especie.strip() != '-' else None),
                'delivery_date': delivery_date,
                'reference_date': reference_date,
                'download_url': download_url,
            }
            documents.append(doc_data)
            docs_found_count += 1
        except Exception as e:
            print(f"AVISO: Erro inesperado ao processar uma linha. Erro: {e}. Linha pulada.")
        
        i += 2
    
    print(f"DEBUG: {docs_found_count} documentos foram extraídos e mapeados com sucesso.")
    return documents


def run_realtime_check(cnpj_map, cvm_code_map):
    html_content = fetch_results_with_playwright()
    if html_content:
        all_documents = parse_cvm_table(html_content, cnpj_map, cvm_code_map)
        if all_documents:
            print(f"Encontrados {len(all_documents)} documentos na consulta para processar.")
            save_to_db(all_documents)
        else:
            print("Nenhum documento válido e mapeável foi encontrado no período.")
    else:
        print("ERRO: Não foi possível obter o conteúdo HTML da página.")

if __name__ == '__main__':
    db_session = Session()
    try:
        cnpj_map, cvm_code_map = get_lookup_maps(db_session)
    finally:
        db_session.close()

    if not cnpj_map or not cvm_code_map:
        print("ERRO CRÍTICO: Mapas não puderam ser carregados. Abortando.")
    else:
        # Comente as 3 linhas de depuração abaixo:
        # print("\n--- EXECUTANDO EM MODO DE DEPURAÇÃO (CICLO ÚNICO COM PLAYWRIGHT) ---")
        # run_realtime_check(cnpj_map, cvm_code_map)
        # print("--- DEPURAÇÃO CONCLUÍDA ---")

        # Descomente as 4 linhas de produção abaixo:
        while True:
            run_realtime_check(cnpj_map, cvm_code_map)
            print(f"Verificação concluída. Aguardando {CHECK_INTERVAL_SECONDS / 60:.0f} minutos para o próximo ciclo...")
            time.sleep(CHECK_INTERVAL_SECONDS)
