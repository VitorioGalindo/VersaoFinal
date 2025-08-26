# /scripts/financials_scraper_package/financials_scraper_user.py

import os
import re
import time
import datetime
import zipfile
import io
import pandas as pd
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright
import logging
import numpy as np
import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

def get_cvm_code_as_int(identifier: str) -> Optional[int]:
    if not identifier: return None
    try:
        numeric_part = re.sub(r'[^\d]', '', str(identifier))
        return int(numeric_part)
    except (ValueError, TypeError):
        return None

class FinancialsScraper:
    def __init__(self, db):
        self.db = db
        self.search_period_days = 15
        self.cvm_url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
        self.SHEET_MAPPING = {
            'DF Ind Ativo': 'BPA_IND', 'DF Ind Passivo': 'BPP_IND', 'DF Ind Resultado Periodo': 'DRE_IND',
            'DF Cons Ativo': 'BPA_CON', 'DF Cons Passivo': 'BPP_CON', 'DF Cons Resultado Periodo': 'DRE_CON',
        }

    def get_lookup_map(self) -> Dict[int, int]:
        from models_user_custom import Company
        logging.info("Mapeando CVM_CODEs para IDs de empresas...")
        # --- CORREÇÃO: Removido o filtro 'is_active' que não existe no modelo ---
        companies = self.db.session.query(Company).filter(Company.cvm_code.isnot(None)).all()
        # --- FIM DA CORREÇÃO ---
        cvm_map = {c.cvm_code: c.id for c in companies}
        logging.info(f"{len(cvm_map)} empresas mapeadas por CVM_CODE.")
        return cvm_map

    def process_excel_file(self, excel_buffer: io.BytesIO, company_id: int, report_type_prefix: str, reference_date: datetime.date, cvm_version: str) -> List:
        from models_user_custom import CvmDocument
        all_financial_lines = []
        try:
            xls = pd.ExcelFile(excel_buffer)
            for sheet_name, report_version in self.SHEET_MAPPING.items():
                if sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
                    df.columns = [str(col).strip().lower() for col in df.columns]
                    rename_map, value_col_name, precision_col_name = {}, None, None
                    for col in df.columns:
                        if 'codigo' in col and 'conta' in col: rename_map[col] = 'account_code'
                        elif 'descri' in col and 'conta' in col: rename_map[col] = 'account_name'
                        elif 'valor' in col and 'atual' in col: value_col_name = col
                        elif 'precisao' in col: precision_col_name = col
                    if not ('account_code' in rename_map.values() and 'account_name' in rename_map.values() and value_col_name): continue
                    df.rename(columns=rename_map, inplace=True)
                    df.dropna(subset=['account_code', value_col_name], inplace=True)
                    for index, row in df.iterrows():
                        account_value_raw = row.get(value_col_name)
                        if pd.isna(account_value_raw): continue
                        multiplier = 1
                        if precision_col_name:
                            precision_val = row.get(precision_col_name, 'Unidade')
                            if isinstance(precision_val, str):
                                p_lower = precision_val.lower()
                                if 'mil' == p_lower: multiplier = 1000
                                elif 'mi' == p_lower: multiplier = 1000000
                        cleaned_str = str(account_value_raw).strip()
                        if cleaned_str.startswith('(') and cleaned_str.endswith(')'): cleaned_str = '-' + cleaned_str[1:-1]
                        cleaned_str = cleaned_str.replace('.', '').replace(',', '.')
                        account_value_np = pd.to_numeric(cleaned_str, errors='coerce')
                        if pd.notna(account_value_np):
                            final_value = account_value_np * multiplier
                            if final_value == 0: continue
                            if isinstance(final_value, (np.int64, np.int32, np.int16)): account_value = int(final_value)
                            elif isinstance(final_value, (np.float64, np.float32)): account_value = float(final_value)
                            else: account_value = final_value
                            account_code_str = str(row['account_code'])
                            is_fixed_bool = len(account_code_str.split('.')) <= 2
                            doc = CvmDocument(
                                company_id=company_id, report_type=report_type_prefix, report_version=report_version,
                                reference_date=reference_date, cvm_version=cvm_version, account_code=account_code_str,
                                account_name=str(row['account_name']), account_value=account_value, is_fixed=is_fixed_bool
                            )
                            all_financial_lines.append(doc)
            return all_financial_lines
        except Exception as e:
            logging.error(f"  -> ERRO ao processar o arquivo Excel: {e}")
            return []

    def _run_check_for_category(self, category_name: str) -> Dict:
        logging.info("="*80)
        logging.info(f"⚙️  INICIANDO SCRAPER (CATEGORIA: {category_name}) ⚙️")
        logging.info("="*80)
        cvm_map = self.get_lookup_map()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
            page = browser.new_page()
            page.set_default_navigation_timeout(90000)
            page.set_default_timeout(60000)
            try:
                page.goto(self.cvm_url, wait_until='domcontentloaded')
                page.locator('input#rdPeriodo').check()
                end_date = datetime.datetime.now()
                start_date = end_date - datetime.timedelta(days=self.search_period_days)
                page.locator('input#txtDataIni').fill(start_date.strftime('%d/%m/%Y'))
                page.locator('input#txtDataFim').fill(end_date.strftime('%d/%m/%Y'))
                
                page.click('#cboCategorias_chosen')
                page.locator(f'li.active-result:has-text("{category_name}")').click()
                page.press('body', 'Escape')
                logging.info(f"✅ Filtro ({category_name}) aplicado.")
                
                page.locator('input#btnConsulta').click()
                logging.info("...Aguardando resultados da consulta...")
                page.wait_for_selector('table#grdDocumentos, .mensagem-sem-resultados', timeout=60000)
                time.sleep(5)
                
                from models_user_custom import CvmDocument
                rows = page.locator('#grdDocumentos tbody tr').all()
                total_new_lines = 0

                for row_locator in rows:
                    cols = row_locator.locator('td').all()
                    if len(cols) < 11: continue
                    
                    cvm_version = cols[8].inner_text().strip()
                    cvm_code_from_site = get_cvm_code_as_int(cols[0].inner_text())
                    company_id = cvm_map.get(cvm_code_from_site)
                    if not company_id: continue

                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', cols[5].inner_text())
                    if not date_match: continue
                    reference_date = datetime.datetime.strptime(date_match.group(1), '%d/%m/%Y').date()
                    
                    exists = self.db.session.query(CvmDocument.id).filter_by(company_id=company_id, report_type=category_name, reference_date=reference_date).first()

                    if not exists:
                        logging.info(f"\n✅ NOVO DOCUMENTO ({category_name} v{cvm_version}): {cols[1].inner_text()} para {reference_date}")
                        try:
                            with page.expect_download() as download_info:
                                cols[10].locator('i[title="Download"]').click()
                            download = download_info.value
                            logging.info(f"  -> Download concluído: {download.suggested_filename}")
                            with open(download.path(), 'rb') as f:
                                with zipfile.ZipFile(io.BytesIO(f.read())) as z:
                                    if 'DadosDocumento.xlsx' in z.namelist():
                                        excel_content = z.read('DadosDocumento.xlsx')
                                        financial_lines = self.process_excel_file(io.BytesIO(excel_content), company_id, category_name, reference_date, cvm_version)
                                        if financial_lines:
                                            self.db.session.bulk_save_objects(financial_lines)
                                            self.db.session.commit()
                                            logging.info(f"  -> 🎉 SUCESSO! {len(financial_lines)} linhas salvas.")
                                            total_new_lines += len(financial_lines)
                        except Exception as e:
                            logging.error(f"  -> ❌ ERRO GERAL: {e}")
                            self.db.session.rollback()

                if total_new_lines > 0:
                    logging.info(f"\n✅ CICLO {category_name} CONCLUÍDO. {total_new_lines} registros salvos.")
                else:
                    logging.info(f"\n✅ Verificação {category_name} concluída. Nenhum dado novo inserido.")
                return {'success': True, 'new_documents': total_new_lines}
            
            except Exception as e:
                logging.critical(f"❌ ERRO INESPERADO no scraper ({category_name}): {e}")
                return {'success': False, 'error': str(e), 'new_documents': 0}
            finally:
                if browser.is_connected():
                    browser.close()

    def run_check_itr(self) -> Dict:
        """Executa a verificação apenas para relatórios ITR."""
        return self._run_check_for_category("ITR")

    def run_check_dfp(self) -> Dict:
        """Executa a verificação apenas para relatórios DFP."""
        return self._run_check_for_category("DFP")