import os
from flask import Blueprint, request, jsonify, abort
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Cria o Blueprint para as rotas de IA
ai_bp = Blueprint('ai_bp', __name__)

# --- Configuração do Gemini ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # Em um ambiente de produção, seria melhor logar este erro
    # do que simplesmente imprimir no console.
    print("ALERTA: A variável de ambiente GOOGLE_API_KEY não foi definida.")
    # Não vamos lançar um erro aqui para permitir que a app inicie mesmo sem a chave,
    # mas as rotas de IA falharão.
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# --- Prompt de Sistema para o Analista Financeiro ---
# Este prompt define a persona e as diretrizes para o modelo de IA.
FINANCIAL_ANALYST_PROMPT = """
Você é o 'Apex Analyst', um analista de research CNPI, especializado no mercado de ações brasileiro. Sua função é analisar empresas de capital aberto (listadas na B3) com base em notícias, relatórios e dados fornecidos no prompt.

**Suas Diretrizes:**
1.  **Análise Fundamentalista:** Forneça análises fundamentalistas detalhadas, focando em múltiplos, resultados financeiros, endividamento, e posição competitiva.
2.  **Riscos e Oportunidades:** Identifique e explique claramente os principais riscos e oportunidades para a empresa em questão.
3.  **Resumo Objetivo:** Resuma os principais acontecimentos recentes relacionados à empresa.
4.  **Baseado em Fatos:** Suas respostas devem ser estritamente baseadas nos fatos, dados e contexto fornecidos. Não especule ou invente informações.
5.  **Linguagem Profissional:** Mantenha um tom profissional, objetivo e técnico.
6.  **Idioma:** Responda sempre em Português do Brasil.
7.  **PROIBIÇÃO:** NÃO FAÇA, sob nenhuma circunstância, RECOMENDAÇÃO DE COMPRA, VENDA OU MANUTENÇÃO de ativos. Apenas forneça a análise técnica e factual.
"""

@ai_bp.route('/ai/analyze', methods=['POST'])
def analyze_company():
    """
    Endpoint para análise de empresas usando IA - rota padrão
    Espera um JSON com dados da empresa para análise
    """
    try:
        if not GOOGLE_API_KEY:
            # Fallback sem IA
            return jsonify({
                "success": True,
                "analysis": {
                    "summary": "Análise de IA indisponível - chave API não configurada",
                    "fundamentals": "Serviço de análise por IA temporariamente indisponível",
                    "risks": ["Serviço de IA não configurado"],
                    "opportunities": ["Configure GOOGLE_API_KEY para análises detalhadas"],
                    "recommendation": "Análise manual recomendada"
                },
                "source": "fallback",
                "ai_available": False
            })

        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Dados não fornecidos para análise"
            }), 400

        # Extrair dados da empresa
        ticker = data.get('ticker', 'N/A')
        company_name = data.get('company_name', 'N/A')
        financial_data = data.get('financial_data', {})
        market_data = data.get('market_data', {})
        news = data.get('news', [])
        
        # Construir prompt para análise
        analysis_prompt = f"""
        {FINANCIAL_ANALYST_PROMPT}
        
        **DADOS PARA ANÁLISE:**
        
        Empresa: {company_name} ({ticker})
        
        Dados Financeiros:
        {financial_data}
        
        Dados de Mercado:
        {market_data}
        
        Notícias Recentes:
        {news}
        
        Por favor, forneça uma análise completa desta empresa seguindo suas diretrizes.
        """
        
        try:
            # Usar Gemini para análise
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(analysis_prompt)
            
            return jsonify({
                "success": True,
                "ticker": ticker,
                "company_name": company_name,
                "analysis": {
                    "full_analysis": response.text,
                    "summary": "Análise gerada por IA",
                    "timestamp": "2025-07-31T00:00:00Z"
                },
                "source": "gemini_ai",
                "ai_available": True
            })
            
        except Exception as ai_error:
            # Fallback se IA falhar
            return jsonify({
                "success": True,
                "ticker": ticker,
                "company_name": company_name,
                "analysis": {
                    "summary": f"Análise da empresa {company_name} ({ticker})",
                    "fundamentals": "Empresa com presença significativa no mercado brasileiro",
                    "risks": ["Volatilidade do mercado", "Riscos macroeconômicos"],
                    "opportunities": ["Crescimento do setor", "Expansão de mercado"],
                    "recommendation": "Análise detalhada recomendada"
                },
                "source": "fallback",
                "ai_available": False,
                "ai_error": str(ai_error)
            })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Erro interno no servidor ao analisar empresa",
            "details": str(e)
        }), 500

@ai_bp.route('/ai/analyst', methods=['POST'])
def ask_financial_analyst():
    """
    Endpoint para receber perguntas para o assistente de análise financeira - rota original
    Espera um JSON com 'history' (uma lista de mensagens) e 'prompt' (a nova pergunta).
    """
    if not GOOGLE_API_KEY:
        abort(503, "Serviço de IA indisponível: a chave de API não foi configurada no servidor.")

    data = request.get_json()
    if not data:
        abort(400, "Requisição inválida: JSON não fornecido.")

    # Extrair o histórico de mensagens e o novo prompt
    history = data.get('history', [])
    user_prompt = data.get('prompt', '')

    if not user_prompt:
        abort(400, "Requisição inválida: 'prompt' é obrigatório.")

    try:
        # Inicializar o modelo Gemini
        model = genai.GenerativeModel('gemini-pro')
        
        # Construir o contexto completo
        full_context = FINANCIAL_ANALYST_PROMPT + "\n\n"
        
        # Adicionar histórico de conversas (se houver)
        for message in history:
            role = message.get('role', 'user')
            content = message.get('content', '')
            full_context += f"{role.upper()}: {content}\n"
        
        # Adicionar a nova pergunta
        full_context += f"USER: {user_prompt}\nASSISTANT:"
        
        # Gerar resposta
        response = model.generate_content(full_context)
        
        return jsonify({
            "success": True,
            "response": response.text,
            "model": "gemini-pro"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Erro ao processar análise",
            "details": str(e)
        }), 500

@ai_bp.route('/ai/sentiment', methods=['POST'])
def analyze_sentiment():
    """Análise de sentimento de notícias ou textos"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Dados não fornecidos"
            }), 400

        text = data.get('text', '')
        if not text:
            return jsonify({
                "success": False,
                "error": "Texto não fornecido para análise"
            }), 400

        # Mock de análise de sentimento
        mock_sentiment = {
            "sentiment": "neutral",
            "confidence": 0.75,
            "positive_score": 0.3,
            "negative_score": 0.2,
            "neutral_score": 0.5,
            "keywords": ["mercado", "empresa", "resultado", "crescimento"],
            "summary": "Sentimento neutro com tendência ligeiramente positiva"
        }
        
        return jsonify({
            "success": True,
            "text_analyzed": text[:100] + "..." if len(text) > 100 else text,
            "sentiment_analysis": mock_sentiment,
            "source": "mock_analysis"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Erro ao analisar sentimento",
            "details": str(e)
        }), 500

@ai_bp.route('/ai/summary', methods=['POST'])
def summarize_text():
    """Resumo automático de textos"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Dados não fornecidos"
            }), 400

        text = data.get('text', '')
        max_length = data.get('max_length', 200)
        
        if not text:
            return jsonify({
                "success": False,
                "error": "Texto não fornecido para resumo"
            }), 400

        # Mock de resumo
        mock_summary = text[:max_length] + "..." if len(text) > max_length else text
        
        return jsonify({
            "success": True,
            "original_length": len(text),
            "summary_length": len(mock_summary),
            "summary": mock_summary,
            "compression_ratio": round(len(mock_summary) / len(text), 2),
            "source": "mock_summary"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Erro ao resumir texto",
            "details": str(e)
        }), 500

@ai_bp.route('/ai/status', methods=['GET'])
def get_ai_status():
    """Status do serviço de IA"""
    try:
        return jsonify({
            "success": True,
            "ai_available": bool(GOOGLE_API_KEY),
            "services": {
                "analysis": True,
                "sentiment": True,
                "summary": True,
                "chat": bool(GOOGLE_API_KEY)
            },
            "model": "gemini-pro" if GOOGLE_API_KEY else "mock",
            "last_updated": "2025-07-31T00:00:00Z"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Erro ao verificar status da IA",
            "details": str(e)
        }), 500