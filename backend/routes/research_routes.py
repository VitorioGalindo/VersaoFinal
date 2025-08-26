import logging
from flask import Blueprint, jsonify, request

from backend.models import db, ResearchNote, Company
from backend.utils.analysis_framework import generate_analysis_framework

logger = logging.getLogger(__name__)
research_bp = Blueprint('research_bp', __name__)

# Log para verificar se o módulo está sendo carregado
logger.info("Módulo de rotas de pesquisa carregado")

# Log para verificar se as rotas estão sendo registradas
logger.info("Registrando rotas de pesquisa")


@research_bp.route('/notes', methods=['GET'])
def list_notes():
    try:
        logger.info("Iniciando listagem de notas de pesquisa")
        notes = ResearchNote.query.order_by(ResearchNote.last_updated.desc()).all()
        logger.info(f"Encontradas {len(notes)} notas")
        data = [
            {
                'id': n.id,
                'title': n.title,
                'content': n.content,
                'last_updated': n.last_updated.isoformat() if n.last_updated else None,
            }
            for n in notes
        ]
        logger.info("Notas processadas com sucesso")
        return jsonify({'success': True, 'notes': data})
    except Exception as e:
        logger.error(f'Erro ao listar notas: {e}', exc_info=True)
        return jsonify({'success': False, 'error': 'Erro ao listar notas'}), 500


@research_bp.route('/notes', methods=['POST'])
def create_note():
    try:
        logger.info("Iniciando criação de nova nota de pesquisa")
        data = request.get_json(silent=True) or {}
        logger.info(f"Dados recebidos: {data}")
        title = data.get('title')
        content = data.get('content', '')
        if not title or content is None:
            logger.warning("Campos obrigatórios não fornecidos")
            return jsonify({'success': False, 'error': 'Campos obrigatórios não fornecidos'}), 400
        logger.info(f"Criando nota com título: {title}")
        note = ResearchNote(title=title, content=content)
        db.session.add(note)
        db.session.commit()
        logger.info(f"Nota criada com sucesso, ID: {note.id}")
        return (
            jsonify(
                {
                    'success': True,
                    'note': {
                        'id': note.id,
                        'title': note.title,
                        'content': note.content,
                        'last_updated': note.last_updated.isoformat() if note.last_updated else None,
                    },
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao criar nota: {e}', exc_info=True)
        return jsonify({'success': False, 'error': 'Erro ao criar nota'}), 500


@research_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id: int):
    try:
        logger.info(f"Iniciando atualização da nota {note_id}")
        data = request.get_json(silent=True) or {}
        logger.info(f"Dados recebidos para atualização: {data}")
        note = ResearchNote.query.get(note_id)
        if not note:
            logger.warning(f"Nota {note_id} não encontrada")
            return jsonify({'success': False, 'error': 'Nota não encontrada'}), 404
        if 'title' in data:
            note.title = data['title']
        if 'content' in data:
            note.content = data['content']
        db.session.commit()
        logger.info(f"Nota {note_id} atualizada com sucesso")
        return jsonify(
            {
                'success': True,
                'note': {
                    'id': note.id,
                    'title': note.title,
                    'content': note.content,
                    'last_updated': note.last_updated.isoformat() if note.last_updated else None,
                },
            }
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao atualizar nota {note_id}: {e}', exc_info=True)
        return jsonify({'success': False, 'error': 'Erro ao atualizar nota'}), 500


@research_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id: int):
    try:
        logger.info(f"Iniciando exclusão da nota {note_id}")
        note = ResearchNote.query.get(note_id)
        if not note:
            logger.warning(f"Nota {note_id} não encontrada")
            return jsonify({'success': False, 'error': 'Nota não encontrada'}), 404
        db.session.delete(note)
        db.session.commit()
        logger.info(f"Nota {note_id} excluída com sucesso")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao deletar nota {note_id}: {e}', exc_info=True)
        return jsonify({'success': False, 'error': 'Erro ao deletar nota'}), 500


@research_bp.route('/generate-company-notes', methods=['POST'])
def generate_company_notes():
    try:
        logger.info("Iniciando geração de notas para empresas")
        
        # Obter todas as empresas
        companies = Company.query.all()
        
        logger.info(f"Encontradas {len(companies)} empresas")
        
        created_notes = []
        for company in companies:
            # Verificar se já existe uma nota para esta empresa
            existing_note = ResearchNote.query.filter(
                ResearchNote.title.like(f"%{company.company_name}%")
            ).first()
            
            if not existing_note:
                # Gerar o framework de análise
                framework = generate_analysis_framework(company)
                
                # Criar a nota
                note_title = f"Análise - {company.company_name}"
                note = ResearchNote(title=note_title, content=framework)
                db.session.add(note)
                created_notes.append(note)
        
        # Commit das notas criadas
        db.session.commit()
        
        # Preparar os dados das notas criadas
        notes_data = [
            {
                'id': note.id,
                'title': note.title,
                'content': note.content,
                'last_updated': note.last_updated.isoformat() if note.last_updated else None,
            }
            for note in created_notes
        ]
        
        logger.info(f"{len(created_notes)} notas criadas com sucesso")
        return jsonify({
            'success': True,
            'notes': notes_data,
            'message': f'{len(created_notes)} notas criadas com sucesso'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao gerar notas para empresas: {e}', exc_info=True)
        return jsonify({'success': False, 'error': 'Erro ao gerar notas para empresas'}), 500


@research_bp.route('/delete-company-notes', methods=['DELETE'])
def delete_company_notes():
    try:
        logger.info("Iniciando exclusão de notas de empresas")
        
        # Obter todas as notas que começam com "Análise - "
        notes = ResearchNote.query.filter(
            ResearchNote.title.like("Análise - %")
        ).all()
        
        logger.info(f"Encontradas {len(notes)} notas de empresas para excluir")
        
        deleted_count = 0
        for note in notes:
            db.session.delete(note)
            deleted_count += 1
        
        # Commit das exclusões
        db.session.commit()
        
        logger.info(f"{deleted_count} notas de empresas excluídas com sucesso")
        return jsonify({
            'success': True,
            'message': f'{deleted_count} notas de empresas excluídas com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao excluir notas de empresas: {e}', exc_info=True)
        return jsonify({'success': False, 'error': 'Erro ao excluir notas de empresas'}), 500
