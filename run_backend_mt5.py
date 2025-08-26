import os
import sys
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

# CARREGAR .ENV ANTES DE TUDO
from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis do arquivo .env

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger(__name__)

# --- Factory Function para a Aplicação ---
def create_app():
    """
    Cria e configura a instância da aplicação Flask.
    Este padrão (Application Factory) é recomendado para evitar importações circulares.
    VERSÃO QUE PRESERVA 100% DO QUE FUNCIONAVA + CARREGA .ENV
    """
    logger.info("🚀 Iniciando a criação da aplicação Flask...")
    
    app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
    
    # Carrega as configurações a partir do objeto Config
    from backend.config import Config
    app.config.from_object(Config)
    
    # Inicializa o SQLAlchemy com a aplicação
    from backend import db
    db.init_app(app)
    
    # Inicializa o CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # --- Importação e Registro de Blueprints (Rotas) ---
    try:
        from backend.routes.companies_routes import companies_routes
        app.register_blueprint(companies_routes, url_prefix='/api/companies')
        logger.info("✅ Rotas de Empresas (companies_routes) carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar companies_routes: {e}")

    try:
        from backend.routes.market_routes import market_routes
        app.register_blueprint(market_routes, url_prefix='/api/market')
        logger.info("✅ Rotas de Mercado (market_routes) carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar market_routes: {e}")

    # ADICIONANDO OUTRAS ROTAS (SEM MEXER NA ESTRUTURA)
    try:
        from backend.routes.documents_routes import documents_bp
        app.register_blueprint(documents_bp, url_prefix='/api')
        logger.info("✅ Documents routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar documents_routes: {e}")

    try:
        from backend.routes.tickers_routes import tickers_bp
        app.register_blueprint(tickers_bp, url_prefix='/api')
        logger.info("✅ Tickers routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar tickers_routes: {e}")

    try:
        from backend.routes.financials_routes import financials_bp
        app.register_blueprint(financials_bp, url_prefix='/api')
        logger.info("✅ Financials routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar financials_routes: {e}")

    try:
        from backend.routes.portfolio_routes import portfolio_bp
        app.register_blueprint(portfolio_bp, url_prefix='/api')
        logger.info("✅ Portfolio routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar portfolio_routes: {e}")

    try:
        from backend.routes.screening_routes import screening_bp
        app.register_blueprint(screening_bp, url_prefix='/api')
        logger.info("✅ Screening routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar screening_routes: {e}")

    try:
        from backend.routes.historical_routes import historical_bp
        app.register_blueprint(historical_bp, url_prefix='/api')
        logger.info("✅ Historical routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar historical_routes: {e}")

    try:
        from backend.routes.macro_routes import macro_bp
        app.register_blueprint(macro_bp, url_prefix='/api')
        logger.info("✅ Macro routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar macro_routes: {e}")

    try:
        from backend.routes.cvm_routes import cvm_bp
        app.register_blueprint(cvm_bp, url_prefix='/api')
        logger.info("✅ CVM routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar cvm_routes: {e}")

    try:
        from backend.routes.search_routes import search_bp
        app.register_blueprint(search_bp, url_prefix='/api')
        logger.info("✅ Search routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar search_routes: {e}")

    try:
        from backend.routes.realtime_routes import realtime_bp
        app.register_blueprint(realtime_bp, url_prefix='/api/realtime')
        logger.info("✅ Realtime routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar realtime_routes: {e}")

    try:
        from backend.routes.ai_routes import ai_bp
        app.register_blueprint(ai_bp, url_prefix='/api')
        logger.info("✅ AI routes carregadas.")
    except Exception as e:
        logger.warning(f"Aviso: Não foi possível importar ai_routes: {e}")
        
    # --- Rotas Básicas e de Verificação ---
    @app.route('/')
    def serve_frontend():
        try:
            return app.send_static_file('index.html')
        except:
            return jsonify({
                "service": "Finance Dashboard Backend",
                "version": "2.0.0",
                "status": "running",
                "message": "Backend funcionando - Frontend não encontrado"
            })

    # HEALTH CHECKS CORRIGIDOS
    @app.route('/health')
    def health_check():
        """Health check básico - CORRIGIDO"""
        try:
            # Testar conexão com banco se possível
            db_status = "unknown"
            try:
                with app.app_context():
                    with db.engine.connect() as conn:
                        conn.execute("SELECT 1")
                    db_status = "connected"
            except:
                db_status = "disconnected"
            
            return jsonify({
                "status": "healthy",
                "service": "Finance Dashboard Backend",
                "version": "2.0.0",
                "database": db_status,
                "metatrader5": "active"
            })
        except Exception as e:
            return jsonify({
                "status": "degraded",
                "service": "Finance Dashboard Backend",
                "error": str(e)
            }), 503

    @app.route('/api/health')
    def api_health_check():
        """Health check da API - PRESERVANDO ESTRUTURA ORIGINAL"""
        try:
            # Testar conexão e contar empresas
            with app.app_context():
                with db.engine.connect() as conn:
                    result = conn.execute("SELECT COUNT(*) FROM companies WHERE is_active = true")
                    company_count = result.scalar()
            
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "total_companies": company_count,
                "message": "Finance Dashboard API funcionando com PostgreSQL"
            })
        except Exception as e:
            return jsonify({
                "status": "degraded",
                "database": "disconnected",
                "error": str(e),
                "message": "Finance Dashboard API com problemas de conectividade"
            }), 503

    @app.errorhandler(404)
    def not_found(e):
        """Handler de erro 404 - CORRIGIDO"""
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Endpoint não encontrado",
                "path": request.path,
                "available_endpoints": [
                    "/api/health",
                    "/api/companies/companies",
                    "/api/companies/count",
                    "/api/market/overview",
                    "/api/market/quotes/<ticker>",
                    "/api/realtime/status",
                    "/api/realtime/quotes"
                ]
            }), 404
        
        # Para rotas não-API, tentar servir frontend
        try:
            return app.send_static_file('index.html')
        except:
            return jsonify({
                "error": "Página não encontrada",
                "message": "Frontend não disponível"
            }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handler de erro 500"""
        return jsonify({
            "error": "Erro interno do servidor",
            "message": "Verifique os logs do servidor"
        }), 500

    logger.info("✅ Flask app criada PRESERVANDO estrutura original")
    return app

# --- Função Principal ---
if __name__ == '__main__':
    logger.info("============================================================")
    logger.info("🚀 FINANCE DASHBOARD BACKEND - VERSÃO COM .ENV CORRIGIDO")
    logger.info("============================================================")
    
    # Verificar dependências críticas
    try:
        import flask
        import flask_cors
        import flask_socketio
        import sqlalchemy
        logger.info("✅ Dependências principais encontradas")
    except ImportError as e:
        logger.error(f"❌ Dependência faltando: {e}")
        exit(1)
    
    # Verificar variáveis de ambiente APÓS carregar .env
    required_env_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️ Variáveis de ambiente faltando: {missing_vars}")
        logger.info("📝 Verificando arquivo .env...")
        
        # Verificar se arquivo .env existe
        if os.path.exists('.env'):
            logger.info("✅ Arquivo .env encontrado")
            # Mostrar algumas variáveis para debug (sem mostrar senhas)
            logger.info(f"🔍 DB_HOST: {os.getenv('DB_HOST', 'NÃO DEFINIDO')}")
            logger.info(f"🔍 DB_USER: {os.getenv('DB_USER', 'NÃO DEFINIDO')}")
            logger.info(f"🔍 DB_NAME: {os.getenv('DB_NAME', 'NÃO DEFINIDO')}")
        else:
            logger.warning("⚠️ Arquivo .env não encontrado")
    else:
        logger.info("✅ Todas as variáveis de ambiente encontradas")
        logger.info(f"🔍 Conectando em: {os.getenv('DB_HOST')}")
    
    try:
        # Criar aplicação Flask
        app = create_app()
        
        # Configurar SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        
        # Inicializar MetaTrader5 RTD Worker (SÓ ISSO É NOVO)
        try:
            from backend.services.metatrader5_rtd_worker import initialize_rtd_worker
            rtd_worker = initialize_rtd_worker(socketio)
            logger.info("✅ MetaTrader5 RTD Worker inicializado")
            logger.info(f"Worker instance: {rtd_worker}")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar MetaTrader5 RTD Worker: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Configurar eventos SocketIO (PRESERVANDO ESTRUTURA)
        from backend.routes.realtime_routes import register_socketio_events
        register_socketio_events(socketio)
        
        # Iniciar servidor
        logger.info("🚀 Servidor pronto! Acesse em http://localhost:5001")
        socketio.run(app, host='0.0.0.0', port=5001, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar aplicação: {e}")
        exit(1)
