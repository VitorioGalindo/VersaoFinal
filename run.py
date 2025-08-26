import os
import sys
import logging
from flask_socketio import SocketIO
from backend import create_app, socketio
from backend.services.metatrader5_rtd_worker import initialize_rtd_worker
from backend.routes.realtime_routes import register_socketio_events

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger(__name__)

# --- INICIALIZAÇÃO DA APLICAÇÃO ---
logger.info("🚀 Iniciando o Servidor do Dashboard Financeiro...")
app = create_app()

# --- INICIALIZAÇÃO DO WORKER DE TEMPO REAL ---
# Esta função (de metatrader5_rtd_worker.py) cria e inicia o worker
# Passamos a instância do socketio para que o worker possa emitir eventos
logger.info("🔧 Inicializando o Worker de Dados em Tempo Real (RTD)...")
initialize_rtd_worker(socketio)

# --- REGISTRO DOS EVENTOS WEBSOCKET ---
# Registra os handlers como @socketio.on('connect'), etc.
logger.info("🔌 Registrando eventos de WebSocket...")
register_socketio_events(socketio)

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5001))

    logger.info(f"✅ Servidor pronto e ouvindo em http://{host}:{port}")
    # Usamos socketio.run() em vez de app.run() para suportar WebSockets
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
