# backend/routes/companies_routes.py
from flask import Blueprint, jsonify, request
from backend.models import Company, Ticker, CvmDocument
from backend import db
import logging

logger = logging.getLogger(__name__)
companies_bp = Blueprint('companies_bp', __name__)

@companies_bp.route('/', methods=['GET'])
def get_companies():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    try:
        paginated_query = db.session.query(Company).order_by(Company.company_name).paginate(page=page, per_page=per_page, error_out=False)
        companies = paginated_query.items
        
        company_list = []
        for company in companies:
            company_list.append({
                'id': company.id,
                'name': company.company_name,
                # CORREÇÃO: Usando a coluna 'ticker' que existe na tabela 'companies'
                'ticker': company.ticker,
                'cnpj': company.cnpj,
                # CORREÇÃO: Usando a coluna 'b3_sector' que existe
                'sector': company.b3_sector
            })

        return jsonify({
            'status': 'success',
            'data': company_list,
            'total': paginated_query.total,
            'page': page,
            'pages': paginated_query.pages
        })
    except Exception as e:
        logger.error(f"Erro detalhado em get_companies: {e}")
        return jsonify({'status': 'error', 'message': 'Erro ao buscar empresas.'}), 500

@companies_bp.route('/<int:company_id>', methods=['GET'])
def get_company_details(company_id):
    try:
        company = db.session.get(Company, company_id)

        if company:
            # O to_dict() do nosso modelo já pega todos os campos corretamente
            return jsonify({'status': 'success', 'data': company.to_dict()})
        
        return jsonify({'status': 'error', 'message': f'Empresa com ID {company_id} não encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes da empresa {company_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Erro ao buscar detalhes da empresa.'}), 500


@companies_bp.route('/<path:cnpj>/documents', methods=['GET'])
def get_company_documents_by_cnpj(cnpj):
    """Retorna documentos da CVM para um CNPJ específico."""

    # Remove caracteres não numéricos do CNPJ para padronizar a consulta
    cnpj_digits = ''.join(filter(str.isdigit, cnpj))
    limit = request.args.get('limit', 25, type=int)

    try:
        company = db.session.query(Company).filter(Company.cnpj == cnpj_digits).first()
        if not company:
            return jsonify({"success": False, "message": f"Empresa com CNPJ {cnpj} não encontrada"}), 404

        docs_query = (
            db.session.query(CvmDocument)
            .filter(CvmDocument.company_id == company.id)
            .order_by(CvmDocument.delivery_date.desc())
            .limit(limit)
        )
        documents = [
            {
                "id": d.id,
                "document_type": d.document_type,
                "title": d.title,
                "delivery_date": d.delivery_date.isoformat() if d.delivery_date else None,
                "download_url": d.download_url,
            }
            for d in docs_query
        ]

        return jsonify({"success": True, "cnpj": cnpj, "company_name": company.company_name, "documents": documents})
    except Exception as e:
        logger.error(f"Erro em get_company_documents_by_cnpj: {e}")
        return jsonify({"success": False, "error": "Erro interno ao buscar documentos"}), 500