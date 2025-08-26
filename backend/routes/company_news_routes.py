import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from backend.models import db, CompanyNewsNote

logger = logging.getLogger(__name__)
company_news_bp = Blueprint('company_news_bp', __name__)


@company_news_bp.route('/<string:ticker>', methods=['GET'])
def list_notes(ticker: str):
    try:
        notes = (
            CompanyNewsNote.query
            .filter_by(ticker=ticker.upper())
            .order_by(CompanyNewsNote.published_at.desc())
            .all()
        )
        return jsonify({'success': True, 'notes': [n.to_dict() for n in notes]})
    except Exception as e:
        logger.error(f'Erro ao listar notas para {ticker}: {e}')
        return jsonify({'success': False, 'error': 'Erro ao listar notas'}), 500


@company_news_bp.route('', methods=['POST'])
def create_note():
    data = request.get_json(silent=True) or {}
    ticker = data.get('ticker')
    title = data.get('title')
    if not ticker or not title:
        return jsonify({'success': False, 'error': 'Campos obrigatórios não fornecidos'}), 400
    try:
        published_at = datetime.fromisoformat(data['published_at']) if data.get('published_at') else None
        note = CompanyNewsNote(
            ticker=ticker.upper(),
            title=title,
            url=data.get('url'),
            source=data.get('source'),
            summary=data.get('summary'),
            content=data.get('content'),
            author=data.get('author'),
            published_at=published_at,
        )
        db.session.add(note)
        db.session.commit()
        return jsonify({'success': True, 'note': note.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao criar nota: {e}')
        return jsonify({'success': False, 'error': 'Erro ao criar nota'}), 500


@company_news_bp.route('/<int:note_id>', methods=['PUT'])
def update_note(note_id: int):
    data = request.get_json(silent=True) or {}
    try:
        note = CompanyNewsNote.query.get(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Nota não encontrada'}), 404
        if 'ticker' in data:
            note.ticker = data['ticker'].upper()
        if 'title' in data:
            note.title = data['title']
        if 'url' in data:
            note.url = data['url']
        if 'source' in data:
            note.source = data['source']
        if 'summary' in data:
            note.summary = data['summary']
        if 'content' in data:
            note.content = data['content']
        if 'author' in data:
            note.author = data['author']
        if 'published_at' in data:
            note.published_at = datetime.fromisoformat(data['published_at']) if data['published_at'] else None
        db.session.commit()
        return jsonify({'success': True, 'note': note.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao atualizar nota {note_id}: {e}')
        return jsonify({'success': False, 'error': 'Erro ao atualizar nota'}), 500


@company_news_bp.route('/<int:note_id>', methods=['DELETE'])
def delete_note(note_id: int):
    try:
        note = CompanyNewsNote.query.get(note_id)
        if not note:
            return jsonify({'success': False, 'error': 'Nota não encontrada'}), 404
        db.session.delete(note)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao deletar nota {note_id}: {e}')
        return jsonify({'success': False, 'error': 'Erro ao deletar nota'}), 500
