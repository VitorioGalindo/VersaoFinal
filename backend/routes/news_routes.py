from flask import Blueprint, jsonify, request
from backend.models import MarketArticle
from textblob import TextBlob

news_bp = Blueprint('news_bp', __name__)


@news_bp.route('/company/<string:ticker>', methods=['GET'])
def get_news_by_ticker(ticker):
    ticker_upper = ticker.upper()
    articles = (
        MarketArticle.query
        .filter(MarketArticle.tickers_relacionados.contains([ticker_upper]))
        .order_by(MarketArticle.data_coleta.desc())
        .all()
    )
    return jsonify([a.to_dict() for a in articles])


@news_bp.route('/latest', methods=['GET'])
def get_latest_news():
    limit = request.args.get('limit', 10, type=int)
    portal = request.args.get('portal')
    order = request.args.get('order', 'desc').lower()

    if order not in ('asc', 'desc'):
        return jsonify({'error': "Parâmetro 'order' inválido"}), 400

    query = MarketArticle.query
    if portal:
        query = query.filter(MarketArticle.portal == portal)

    order_field = MarketArticle.data_coleta
    order_clause = order_field.asc() if order == 'asc' else order_field.desc()
    articles = query.order_by(order_clause).limit(limit).all()
    return jsonify([a.to_dict() for a in articles])


@news_bp.route('/<int:article_id>/analyze', methods=['POST'])
def analyze_news_article(article_id):
    article = MarketArticle.query.get_or_404(article_id)
    text = article.conteudo_completo or article.resumo or ''
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        sentiment = 'Positivo'
    elif polarity < -0.1:
        sentiment = 'Negativo'
    else:
        sentiment = 'Neutro'

    return jsonify({
        'sentiment': sentiment,
        'summary': text[:200],
        'mentionedCompanies': [],
        'relatedNews': []
    })
