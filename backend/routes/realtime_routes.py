import logging
from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room
from backend.services.metatrader5_rtd_worker import get_rtd_worker

logger = logging.getLogger(__name__)
realtime_bp = Blueprint('realtime_bp', __name__)

# --- ROTAS HTTP ---
@realtime_bp.route('/status', methods=['GET'])
def get_realtime_status_http():
    worker = get_rtd_worker()
    logger.debug(f"Getting realtime status, worker: {worker}")
    if not worker:
        return jsonify({'status': 'error', 'message': 'Worker não inicializado'}), 503
    stats = worker.get_subscription_stats()
    return jsonify({'status': 'success', 'data': stats})


@realtime_bp.route('/quotes', methods=['GET'])
def get_realtime_quotes_http():
    """Retorna cotações em tempo real para uma lista de tickers."""
    worker = get_rtd_worker()
    if not worker or not worker.mt5_connected:
        return jsonify({'status': 'error', 'message': 'Worker não inicializado'}), 503

    tickers = request.args.getlist("tickers") or ["VALE3", "PETR4", "ITUB4"]

    quotes = {}
    for t in tickers:
        quote = worker.get_mt5_quote(t.upper())
        if quote:
            quotes[t.upper()] = quote
    return jsonify({'status': 'success', 'data': quotes})

# --- EVENTOS WEBSOCKET ---
def register_socketio_events(socketio):
    worker = get_rtd_worker()

    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Cliente conectado via WebSocket: {request.sid}")
        emit('connected', {'status': 'success', 'sid': request.sid})

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Cliente desconectado: {request.sid}")
        if worker and hasattr(worker, 'active_subscriptions') and request.sid in worker.active_subscriptions:
            del worker.active_subscriptions[request.sid]

    @socketio.on('subscribe_quotes')
    def handle_subscribe(data):
        sid = request.sid
        tickers = data.get('tickers', [])
        if not isinstance(tickers, list) or not worker:
            logger.warning(f"Invalid subscribe request from {sid}: {data}")
            return
        
        join_room(sid)
        for ticker in tickers:
            if isinstance(ticker, str):
                worker.subscribe_ticker(sid, ticker.upper())
        logger.info(f"Sessão {sid} subscreveu para: {tickers}")
        emit('subscription_confirmed', {'tickers': tickers})

    @socketio.on('unsubscribe_quotes')
    def handle_unsubscribe(data):
        sid = request.sid
        tickers = data.get('tickers', [])
        if not isinstance(tickers, list) or not worker:
            return
            
        for ticker in tickers:
            if isinstance(ticker, str):
                worker.unsubscribe_ticker(sid, ticker.upper())
        logger.info(f"Sessão {sid} cancelou subscrição de: {tickers}")
        emit('unsubscription_confirmed', {'tickers': tickers})

