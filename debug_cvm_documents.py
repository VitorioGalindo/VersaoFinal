# Script para testar partes específicas da função list_cvm_documents
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend import create_app, db
from backend.models import CvmDocument, Company
from sqlalchemy import func
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_query():
    app = create_app()
    
    with app.app_context():
        try:
            print("Testando consulta básica...")
            
            # Testar a consulta exata usada na função list_cvm_documents
            query = db.session.query(CvmDocument, Company.company_name).outerjoin(
                Company, CvmDocument.company_id == Company.id
            )
            
            print("Consulta criada com sucesso")
            
            # Aplicar limit
            query = query.order_by(CvmDocument.delivery_date.desc()).limit(50)
            print("Ordenação e limite aplicados")
            
            # Executar consulta
            docs = query.all()
            print(f"Consulta executada com sucesso. Encontrados {len(docs)} documentos.")
            
            # Processar resultados
            documents = []
            for doc, company_name in docs:
                delivery = (
                    doc.delivery_date.isoformat()
                    if hasattr(doc.delivery_date, "isoformat")
                    else doc.delivery_date
                )
                documents.append(
                    {
                        "id": doc.id,
                        "company_name": company_name or "",
                        "document_type": doc.document_type,
                        "category": doc.category,
                        "title": doc.title,
                        "delivery_date": delivery,
                        "download_url": doc.download_url,
                    }
                )
            
            print("Documentos processados com sucesso")
            print(f"Primeiro documento: {documents[0] if documents else 'Nenhum'}")
            
        except Exception as e:
            logger.exception("Erro durante o teste: %s", e)
            print(f"Erro: {e}")

if __name__ == "__main__":
    test_query()