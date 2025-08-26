import logging
from datetime import date
from flask import Blueprint, jsonify, request
from sqlalchemy.sql import func

from backend.models import (
    db,
    Portfolio,
    PortfolioPosition,
    AssetMetrics,
    PortfolioDailyValue,
    PortfolioEditableMetric,
    Ticker,
    Company,
)

logger = logging.getLogger(__name__)
portfolio_bp = Blueprint("portfolio_bp", __name__)


def calculate_portfolio_summary(portfolio_id: int):
    """Calcula o resumo e holdings do portfólio."""
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return None

        positions = (
            PortfolioPosition.query.filter_by(portfolio_id=portfolio_id)
            .join(
                AssetMetrics,
                PortfolioPosition.symbol == AssetMetrics.symbol,
                isouter=True,
            )
            .all()
        )

        holdings = []
        total_value = 0.0
        total_cost = 0.0
        total_long = 0.0
        total_short = 0.0
        
        # Log para debug
        logger.info(f"Iniciando cálculo do portfólio {portfolio_id}")
        logger.info(f"Número de posições encontradas: {len(positions)}")
        for pos in positions:
            # Tratamento mais robusto para valores ausentes
            last_price = 0.0
            daily_change_pct = 0.0
            
            if pos.metrics:
                try:
                    # Obter o preço atual do ativo
                    last_price = float(pos.metrics.last_price) if pos.metrics.last_price is not None else 0.0

                    # Usar a nova coluna previous_close_correct se disponível
                    previous_close = pos.metrics.get_previous_close() or 0.0
                    open_price = float(pos.metrics.open_price) if pos.metrics.open_price is not None else 0.0
                    logger.debug(
                        f"Dados do banco para {pos.symbol}: last_price={last_price}, previous_close={previous_close}, open_price={open_price}"
                    )

                    # Calcular a variação diária corretamente usando o fechamento anterior
                    if previous_close and previous_close != 0:
                        daily_change_pct = ((last_price / previous_close) - 1) * 100
                        logger.debug(
                            f"Calculando variação para {pos.symbol}: last_price={last_price}, previous_close={previous_close}, variação={daily_change_pct:.4f}%"
                        )
                    else:
                        daily_change_pct = 0.0
                        logger.debug(
                            f"Sem previous_close para {pos.symbol}: last_price={last_price}, previous_close={previous_close}"
                        )
                        # Verificar se temos open_price como fallback
                        if open_price and open_price != 0:
                            daily_change_pct = ((last_price / open_price) - 1) * 100
                            logger.debug(
                                f"Usando open_price como fallback para {pos.symbol}: last_price={last_price}, open_price={open_price}, variação={daily_change_pct:.4f}%"
                            )
                except (ValueError, TypeError, ZeroDivisionError) as e:
                    last_price = 0.0
                    daily_change_pct = 0.0
                    logger.error(f"Erro ao calcular variação para {pos.symbol}: {e}")

                # Fallback: se ainda não obtivemos variação e há price_change_percent
                if daily_change_pct == 0.0:
                    try:
                        pct = (
                            float(pos.metrics.price_change_percent)
                            if pos.metrics.price_change_percent is not None
                            else 0.0
                        )
                        if pct != 0.0:
                            daily_change_pct = pct
                    except (ValueError, TypeError):
                        pass
            else:
                last_price = 0.0
                daily_change_pct = 0.0

            quantity = float(pos.quantity) if pos.quantity is not None else 0.0
            avg_price = float(pos.avg_price) if pos.avg_price is not None else 0.0
            target_weight = float(pos.target_weight) if pos.target_weight is not None else 0.0
            
            # Log para depuração
            logger.debug(f"Valores da posição {pos.symbol}: quantity={quantity}, avg_price={avg_price}, target_weight={target_weight}")

            position_value = quantity * last_price
            cost = quantity * avg_price
            gain = position_value - cost
            gain_percent = (gain / cost * 100) if cost else 0.0

            holdings.append(
                {
                    "symbol": pos.symbol,
                    "quantity": quantity,
                    "avg_price": avg_price,
                    "last_price": last_price,
                    "daily_change_pct": daily_change_pct,
                    "position_value": position_value,
                    "value": position_value,
                    "cost": cost,
                    "gain": gain,
                    "gain_percent": gain_percent,
                    "contribution": 0.0,
                    "position_pct": 0.0,
                    "target_pct": target_weight,  # Usando target_weight
                    "difference": 0.0,
                    "adjustment_qty": 0.0,
                }
            )

            total_value += position_value
            total_cost += cost
            if position_value >= 0:
                total_long += position_value
            else:
                total_short += position_value
                
        # Log após o cálculo das posições
        logger.info(f"Total value after positions: {total_value}")
        logger.info(f"Total cost after positions: {total_cost}")
        logger.info(f"Total long after positions: {total_long}")
        logger.info(f"Total short after positions: {total_short}")

        # Calcula campos dependentes do valor total
        try:
            total_value = float(total_value) if total_value is not None else 0.0
        except (ValueError, TypeError):
            total_value = 0.0
            
        for h in holdings:
            try:
                # Inicialmente apenas garantir que position_pct esteja presente; será recalculado depois
                position_value = float(h["position_value"]) if h["position_value"] is not None else 0.0
                position_pct = (position_value / total_value * 100) if total_value and total_value != 0 else 0.0
                h["position_pct"] = position_pct
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.error(f"Erro no cálculo inicial das métricas para holding {h.get('symbol', 'unknown')}: {e}")
                h["position_pct"] = 0.0

        # Garantir que os valores sejam números válidos
        try:
            total_value = float(total_value) if total_value is not None else 0.0
        except (ValueError, TypeError):
            total_value = 0.0
            
        try:
            total_cost = float(total_cost) if total_cost is not None else 0.0
        except (ValueError, TypeError):
            total_cost = 0.0

        total_gain = total_value - total_cost
        total_gain_percent = (total_gain / total_cost * 100) if total_cost and total_cost != 0 else 0.0

        today = date.today()
        # Removendo o acesso à tabela PortfolioDailyMetric que não existe
        metrics = {}

        # Obter valores editáveis diretamente da tabela portfolio_editable_metrics
        try:
            editable_metrics = {}
            
            # Primeiro tentar buscar métricas para a data atual
            editable_metrics_records = PortfolioEditableMetric.query.filter_by(
                portfolio_id=portfolio_id, date=today
            ).all()
            
            # Se não encontrar métricas para a data atual, buscar a data mais recente disponível
            if not editable_metrics_records:
                logger.info(f"Não encontradas métricas para {today} no cálculo do portfólio, buscando data mais recente...")
                latest_metric = PortfolioEditableMetric.query.filter_by(
                    portfolio_id=portfolio_id
                ).order_by(PortfolioEditableMetric.date.desc()).first()
                
                if latest_metric:
                    latest_date = latest_metric.date
                    logger.info(f"Encontrada data mais recente para métricas: {latest_date}")
                    editable_metrics_records = PortfolioEditableMetric.query.filter_by(
                        portfolio_id=portfolio_id, date=latest_date
                    ).all()
                else:
                    logger.info("Nenhuma métrica encontrada no banco de dados para o cálculo do portfólio")
                    editable_metrics_records = []
            else:
                logger.info(f"Registros de métricas editáveis encontrados: {len(editable_metrics_records)}")
            
            for record in editable_metrics_records:
                try:
                    editable_metrics[record.metric_key] = float(record.metric_value) if record.metric_value is not None else 0.0
                    logger.info(f"Metric {record.metric_key}: {record.metric_value}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Erro ao converter valor da métrica {record.metric_key}: {e}")
                    editable_metrics[record.metric_key] = 0.0
            
            cota_d1 = editable_metrics.get("cotaD1", 0.0)
            qtd_cotas = editable_metrics.get("qtdCotas", 0.0)
            caixa_bruto = editable_metrics.get("caixaBruto", 0.0)
            
            # Garantir que os valores sejam números válidos
            try:
                cota_d1 = float(cota_d1) if cota_d1 is not None else 0.0
            except (ValueError, TypeError):
                cota_d1 = 0.0
                
            try:
                qtd_cotas = float(qtd_cotas) if qtd_cotas is not None else 0.0
            except (ValueError, TypeError):
                qtd_cotas = 0.0
                
            try:
                caixa_bruto = float(caixa_bruto) if caixa_bruto is not None else 0.0
            except (ValueError, TypeError):
                caixa_bruto = 0.0
            
            # Log para depuração
            logger.info(f"Dados para cálculo da cota - patrimonio_liquido: {total_value}, qtd_cotas: {qtd_cotas}, cota_d1: {cota_d1}")
        except Exception as e:
            logger.error(f"Erro ao obter métricas editáveis: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            cota_d1 = 0.0
            qtd_cotas = 0.0
            caixa_bruto = 0.0

        patrimonio_liquido = total_value
        # Garantir que os valores sejam números válidos
        try:
            patrimonio_liquido = float(patrimonio_liquido) if patrimonio_liquido is not None else 0.0
        except (ValueError, TypeError):
            patrimonio_liquido = 0.0
            
        # Log antes do cálculo do patrimônio líquido ajustado
        logger.info(f"Patrimônio líquido antes do ajuste: {patrimonio_liquido}")
        logger.info(f"Caixa bruto: {caixa_bruto}")
        
        # Ajustar o patrimônio líquido com a caixa bruta
        # O patrimonio_liquido representa o valor das posições
        # A caixa bruta precisa ser adicionada para obter o patrimônio líquido total
        patrimonio_liquido_ajustado = patrimonio_liquido + caixa_bruto
        logger.info(f"Patrimônio líquido ajustado (com caixa): {patrimonio_liquido_ajustado}")

        # Recalcular position_pct e diferença com base no patrimônio líquido ajustado
        for h in holdings:
            try:
                position_value = float(h["position_value"]) if h["position_value"] is not None else 0.0
                target_pct = float(h["target_pct"]) if h["target_pct"] is not None else 0.0
                position_pct = (
                    (position_value / patrimonio_liquido_ajustado) * 100
                    if patrimonio_liquido_ajustado and patrimonio_liquido_ajustado != 0
                    else 0.0
                )
                h["position_pct"] = position_pct
                h["difference"] = target_pct - position_pct
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.error(
                    f"Erro no recálculo das métricas para holding {h.get('symbol', 'unknown')}: {e}"
                )
                h["position_pct"] = 0.0
                h["difference"] = 0.0

        # Calcular a contribuição de cada ativo para a variação diária e o ajuste necessário
        # Contribuição = (valor da variação da posição no ativo / patrimonio_liquido_ajustado) * 100
        for h in holdings:
            try:
                position_value = float(h["position_value"]) if h["position_value"] is not None else 0.0
                daily_pct = float(h["daily_change_pct"]) if h["daily_change_pct"] is not None else 0.0
                diff_pct = float(h["difference"]) if h["difference"] is not None else 0.0
                last_price = float(h["last_price"]) if h["last_price"] is not None else 0.0

                daily_change_value = position_value * daily_pct / 100
                if patrimonio_liquido_ajustado and patrimonio_liquido_ajustado != 0:
                    h["contribution"] = (daily_change_value / patrimonio_liquido_ajustado) * 100
                    h["adjustment_qty"] = (
                        (diff_pct / 100 * patrimonio_liquido_ajustado) / last_price
                        if last_price
                        else 0.0
                    )
                else:
                    h["contribution"] = 0.0
                    h["adjustment_qty"] = 0.0
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.error(
                    f"Erro no cálculo da contribuição/ajuste para holding {h.get('symbol', 'unknown')}: {e}"
                )
                h["contribution"] = 0.0
                h["adjustment_qty"] = 0.0
        
        # Usar o patrimônio líquido ajustado para os cálculos
        logger.info(f"Usando patrimonio_liquido_ajustado para cálculos: {patrimonio_liquido_ajustado}")
            
        try:
            qtd_cotas = float(qtd_cotas) if qtd_cotas is not None else 0.0
        except (ValueError, TypeError):
            qtd_cotas = 0.0

        # Log detalhado antes do cálculo
        logger.info(f"Valores antes do cálculo da cota - patrimonio_liquido_ajustado: {patrimonio_liquido_ajustado}, qtd_cotas: {qtd_cotas}")
        logger.info(f"Tipo de patrimonio_liquido_ajustado: {type(patrimonio_liquido_ajustado)}, tipo de qtd_cotas: {type(qtd_cotas)}")
        if qtd_cotas and qtd_cotas != 0:
            try:
                resultado_divisao = patrimonio_liquido_ajustado / qtd_cotas
                logger.info(f"Divisão: {patrimonio_liquido_ajustado} / {qtd_cotas} = {resultado_divisao}")
                valor_cota = resultado_divisao
            except (ZeroDivisionError, ValueError, TypeError) as e:
                logger.error(f"Erro na divisão para cálculo da cota: {e}")
                valor_cota = 0.0
        else:
            logger.info("qtd_cotas é zero ou None, definindo valor_cota como 0.0")
            valor_cota = 0.0
        logger.info(f"Valor da cota calculado: {valor_cota}")
        
        # Log adicional para debug
        logger.info(f"Valores para cálculo da variação da cota - valor_cota: {valor_cota}, cota_d1: {cota_d1}")
        if cota_d1 and cota_d1 != 0:
            try:
                variacao = ((valor_cota / cota_d1) - 1) * 100
                logger.info(f"Variação da cota: (({valor_cota} / {cota_d1}) - 1) * 100 = {variacao}")
                variacao_cota_pct = variacao
            except (ZeroDivisionError, ValueError, TypeError) as e:
                logger.error(f"Erro no cálculo da variação da cota: {e}")
                variacao_cota_pct = 0.0
        else:
            logger.info("cota_d1 é zero ou None, definindo variacao_cota_pct como 0.0")
            variacao_cota_pct = 0.0
        logger.info(f"Variação da cota calculada: {variacao_cota_pct}")
        # Garantir que os valores sejam números válidos
        try:
            valor_cota = float(valor_cota) if valor_cota is not None else 0.0
        except (ValueError, TypeError):
            valor_cota = 0.0
            
        try:
            cota_d1 = float(cota_d1) if cota_d1 is not None else 0.0
        except (ValueError, TypeError):
            cota_d1 = 0.0

        try:
            variacao_cota_pct = float(variacao_cota_pct) if variacao_cota_pct is not None else 0.0
        except (ValueError, TypeError):
            variacao_cota_pct = 0.0
            
        try:
            total_long = float(total_long) if total_long is not None else 0.0
        except (ValueError, TypeError):
            total_long = 0.0
            
        try:
            total_short = float(total_short) if total_short is not None else 0.0
        except (ValueError, TypeError):
            total_short = 0.0
            
        try:
            caixa_bruto = float(caixa_bruto) if caixa_bruto is not None else 0.0
        except (ValueError, TypeError):
            caixa_bruto = 0.0
            
        try:
            patrimonio_liquido_ajustado = float(patrimonio_liquido_ajustado) if patrimonio_liquido_ajustado is not None else 0.0
        except (ValueError, TypeError):
            patrimonio_liquido_ajustado = 0.0

        # Log adicional para os cálculos de posição
        logger.info(f"Cálculos de posição - total_long: {total_long}, total_short: {total_short}, caixa_bruto: {caixa_bruto}")
        logger.info(f"Valores antes dos cálculos de posição - patrimonio_liquido_ajustado: {patrimonio_liquido_ajustado}")

        # Ajustar os cálculos para considerar o caixa como redutor
        # O caixa reduz a posição comprada e a exposição total
        logger.info(f"Valores para cálculo de posição - total_long: {total_long}, caixa_bruto: {caixa_bruto}, patrimonio_liquido_ajustado: {patrimonio_liquido_ajustado}")
        if patrimonio_liquido_ajustado and patrimonio_liquido_ajustado != 0:
            try:
                posicao_comprada_pct = ((total_long - caixa_bruto) / patrimonio_liquido_ajustado * 100)
                posicao_vendida_pct = (abs(total_short) / patrimonio_liquido_ajustado * 100)
                logger.info(f"Posição comprada calculada: {posicao_comprada_pct}, posição vendida: {posicao_vendida_pct}")
            except (ZeroDivisionError, ValueError, TypeError) as e:
                logger.error(f"Erro no cálculo das posições: {e}")
                posicao_comprada_pct = 0.0
                posicao_vendida_pct = 0.0
        else:
            posicao_comprada_pct = 0.0
            posicao_vendida_pct = 0.0
            logger.info("patrimonio_liquido_ajustado é zero, definindo posições como 0.0")
        
        try:
            net_long_pct = posicao_comprada_pct - posicao_vendida_pct
            logger.info(f"Net long calculado: {net_long_pct}")
        except (ValueError, TypeError) as e:
            logger.error(f"Erro no cálculo do net long: {e}")
            net_long_pct = 0.0
            
        if patrimonio_liquido_ajustado and patrimonio_liquido_ajustado != 0:
            try:
                exposicao_total_pct = ((total_long - caixa_bruto + abs(total_short)) / patrimonio_liquido_ajustado * 100)
                logger.info(f"Exposição total calculada: {exposicao_total_pct}")
            except (ZeroDivisionError, ValueError, TypeError) as e:
                logger.error(f"Erro no cálculo da exposição total: {e}")
                exposicao_total_pct = 0.0
        else:
            exposicao_total_pct = 0.0
            logger.info("patrimonio_liquido_ajustado é zero, definindo exposição total como 0.0")
            
        # Log dos valores finais
        logger.info(f"VALORES FINAIS CALCULADOS:")
        logger.info(f"  patrimonio_liquido_ajustado: {patrimonio_liquido_ajustado}")
        logger.info(f"  valor_cota: {valor_cota}")
        logger.info(f"  variacao_cota_pct: {variacao_cota_pct}")
        logger.info(f"  posicao_comprada_pct: {posicao_comprada_pct}")
        logger.info(f"  posicao_vendida_pct: {posicao_vendida_pct}")
        logger.info(f"  net_long_pct: {net_long_pct}")
        logger.info(f"  exposicao_total_pct: {exposicao_total_pct}")
            
        # Log dos valores finais das posições
        logger.info(f"Valores finais das posições:")
        logger.info(f"  posicao_comprada_pct: {posicao_comprada_pct}")
        logger.info(f"  posicao_vendida_pct: {posicao_vendida_pct}")
        logger.info(f"  net_long_pct: {net_long_pct}")
        logger.info(f"  exposicao_total_pct: {exposicao_total_pct}")

        summary = {
            "id": portfolio.id if portfolio else portfolio_id,
            "name": portfolio.name if portfolio else f"Portfolio {portfolio_id}",
            "total_value": total_value,
            "total_cost": total_cost,
            "total_gain": total_gain,
            "total_gain_percent": total_gain_percent,
            "holdings": holdings,
            "patrimonio_liquido": patrimonio_liquido_ajustado,  # Usar o valor ajustado
            "valor_cota": valor_cota,
            "variacao_cota_pct": variacao_cota_pct,
            "posicao_comprada_pct": posicao_comprada_pct,
            "posicao_vendida_pct": posicao_vendida_pct,
            "net_long_pct": net_long_pct,
            "exposicao_total_pct": exposicao_total_pct,
        }
        
        # Log para depuração
        logger.debug(f"Resumo do portfólio {portfolio_id}:")
        logger.debug(f"  Total de holdings: {len(holdings)}")
        for holding in holdings:
            logger.debug(f"  Holding {holding['symbol']}: quantity={holding['quantity']}, target_pct={holding['target_pct']}")
        
        # Log específico para os valores da cota
        logger.info(f"VALORES FINAIS DO PORTFÓLIO {portfolio_id}:")
        logger.info(f"  patrimonio_liquido: {patrimonio_liquido_ajustado}")
        logger.info(f"  valor_cota: {valor_cota}")
        logger.info(f"  variacao_cota_pct: {variacao_cota_pct}")
        logger.info(f"  posicao_comprada_pct: {posicao_comprada_pct}")
        logger.info(f"  posicao_vendida_pct: {posicao_vendida_pct}")
        logger.info(f"  net_long_pct: {net_long_pct}")
        logger.info(f"  exposicao_total_pct: {exposicao_total_pct}")
        
        return summary
    except Exception as e:
        logger.error(f"Erro em calculate_portfolio_summary: {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise


@portfolio_bp.route("/<int:portfolio_id>/summary", methods=["GET"])
def get_portfolio_summary(portfolio_id: int):
    """Retorna apenas os holdings de um portfólio."""
    try:
        logger.info(f"Iniciando obtenção dos holdings do portfólio {portfolio_id}")
        summary = calculate_portfolio_summary(portfolio_id)
        if not summary:
            logger.info(f"Portfólio {portfolio_id} não encontrado, criando padrão")
            # Criar um portfólio padrão se não existir
            portfolio = Portfolio.query.get(portfolio_id)
            if not portfolio:
                portfolio = Portfolio(id=portfolio_id, name=f"Portfolio {portfolio_id}")
                db.session.add(portfolio)
                db.session.commit()
            
            summary = {
                "id": portfolio.id,
                "name": portfolio.name,
                "total_value": 0.0,
                "total_cost": 0.0,
                "total_gain": 0.0,
                "total_gain_percent": 0.0,
                "holdings": [],
            }

        # Retornar apenas os holdings
        holdings_data = {
            "id": summary["id"],
            "name": summary["name"],
            "total_value": summary["total_value"],
            "total_cost": summary["total_cost"],
            "total_gain": summary["total_gain"],
            "total_gain_percent": summary["total_gain_percent"],
            "holdings": summary["holdings"],
        }

        # Log para depuração
        logger.debug(f"Retornando holdings do portfólio {portfolio_id}:")
        logger.debug(f"  Holdings: {holdings_data.get('holdings', [])}")
        
        return jsonify({"success": True, "portfolio": holdings_data})
    except Exception as e:
        logger.error(f"Erro em get_portfolio_summary para portfolio_id {portfolio_id}: {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return (
            jsonify({"success": False, "error": "Erro interno ao buscar holdings do portfólio", "details": str(e)}),
            500,
        )


@portfolio_bp.route("/<int:portfolio_id>/positions", methods=["POST"])
def upsert_positions(portfolio_id: int):
    """Insere, atualiza ou remove posições de um portfólio."""
    data = request.get_json(silent=True) or []
    if not isinstance(data, list):
        return jsonify({"success": False, "error": "Formato inválido"}), 400

    try:
        # Garante que todos os tickers existam ou cria novos
        for item in data:
            symbol = item.get("symbol")
            if not symbol:
                continue
            ticker = Ticker.query.filter_by(symbol=symbol).first()
            if not ticker:
                # Se o ticker não existe, cria um novo com tipo padrão 'stock'
                ticker_type = item.get("type", "stock")  # Define 'stock' como padrão se não fornecido
                ticker = Ticker(symbol=symbol, type=ticker_type, company_id=None)
                db.session.add(ticker)

        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            portfolio = Portfolio(id=portfolio_id, name=f"Portfolio {portfolio_id}")
            db.session.add(portfolio)

        # Obter todos os símbolos que estão sendo enviados
        symbols_to_keep = [item.get("symbol") for item in data if item.get("symbol")]
        
        # Remover posições que não estão na lista enviada
        if symbols_to_keep:
            positions_to_remove = PortfolioPosition.query.filter(
                PortfolioPosition.portfolio_id == portfolio_id,
                ~PortfolioPosition.symbol.in_(symbols_to_keep)
            ).all()
        else:
            # Se não há posições enviadas, remover todas
            positions_to_remove = PortfolioPosition.query.filter_by(
                portfolio_id=portfolio_id
            ).all()
        
        for position in positions_to_remove:
            db.session.delete(position)

        # Inserir ou atualizar posições
        for item in data:
            symbol = item.get("symbol")
            quantity = item.get("quantity", 0)
            avg_price = item.get("avg_price", 0)
            target_weight = item.get("target_weight", 0)  # Adicionando target_weight
            if not symbol:
                continue

            position = PortfolioPosition.query.filter_by(
                portfolio_id=portfolio_id, symbol=symbol
            ).first()
            if position:
                position.quantity = quantity
                position.avg_price = avg_price
                position.target_weight = target_weight  # Atualizando target_weight
                logger.debug(f"Atualizando posição {symbol}: quantity={quantity}, avg_price={avg_price}, target_weight={target_weight}")
            else:
                new_position = PortfolioPosition(
                    portfolio=portfolio,
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=avg_price,
                    target_weight=target_weight,  # Adicionando target_weight
                )
                db.session.add(new_position)
                logger.debug(f"Criando nova posição {symbol}: quantity={quantity}, avg_price={avg_price}, target_weight={target_weight}")

        # Log para verificar as posições antes de salvar
        positions = PortfolioPosition.query.filter_by(portfolio_id=portfolio_id).all()
        logger.debug(f"Posições antes do commit para portfolio {portfolio_id}:")
        for pos in positions:
            logger.debug(f"  {pos.symbol}: quantity={pos.quantity}, avg_price={pos.avg_price}, target_weight={pos.target_weight}")
        
        db.session.commit()
        
        # Log para verificar as posições após salvar
        positions = PortfolioPosition.query.filter_by(portfolio_id=portfolio_id).all()
        logger.debug(f"Posições após commit para portfolio {portfolio_id}:")
        for pos in positions:
            logger.debug(f"  {pos.symbol}: quantity={pos.quantity}, avg_price={pos.avg_price}, target_weight={pos.target_weight}")
        
        return jsonify({"success": True}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao inserir posições: {e}")
        return (
            jsonify({"success": False, "error": "Erro ao inserir posições"}),
            500,
        )


@portfolio_bp.route("/<int:portfolio_id>/snapshot", methods=["POST"])
def create_portfolio_snapshot(portfolio_id: int):
    """Salva um snapshot diário do valor do portfólio."""
    try:
        summary = calculate_portfolio_summary(portfolio_id)
        if not summary:
            return (
                jsonify({"success": False, "error": "Portfólio não encontrado"}),
                404,
            )

        record = PortfolioDailyValue.query.filter_by(
            portfolio_id=portfolio_id, date=func.current_date()
        ).first()

        if record:
            record.total_value = summary["total_value"]
            record.total_cost = summary["total_cost"]
            record.total_gain = summary["total_gain"]
            record.total_gain_percent = summary["total_gain_percent"]
        else:
            db.session.add(
                PortfolioDailyValue(
                    portfolio_id=portfolio_id,
                    total_value=summary["total_value"],
                    total_cost=summary["total_cost"],
                    total_gain=summary["total_gain"],
                    total_gain_percent=summary["total_gain_percent"],
                )
            )

        db.session.commit()
        return jsonify({"success": True}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar snapshot: {e}")
        return (
            jsonify({"success": False, "error": "Erro ao salvar snapshot"}),
            500,
        )


@portfolio_bp.route("/<int:portfolio_id>/daily-metrics", methods=["POST"])
def update_daily_metrics(portfolio_id: int):
    """Atualiza métricas diárias do portfólio."""
    data = request.get_json(silent=True) or []
    if not isinstance(data, list):
        return jsonify({"success": False, "error": "Formato inválido"}), 400

    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return (
                jsonify({"success": False, "error": "Portfólio não encontrado"}),
                404,
            )

        today = date.today()
        for item in data:
            metric_id = item.get("id")
            value = item.get("value")
            if metric_id is None or value is None:
                continue

            record = PortfolioDailyMetric.query.filter_by(
                portfolio_id=portfolio_id, metric_id=metric_id, date=today
            ).first()

            if record:
                record.value = value
            else:
                db.session.add(
                    PortfolioDailyMetric(
                        portfolio_id=portfolio_id,
                        metric_id=metric_id,
                        value=value,
                        date=today,
                    )
                )

        db.session.commit()
        return jsonify({"success": True}), 201
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao salvar métricas", exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao salvar métricas",
                    "detail": str(e),
                }
            ),
            500,
        )


@portfolio_bp.route("/<int:portfolio_id>/daily-values", methods=["GET"])
def get_portfolio_daily_values(portfolio_id: int):
    """Retorna a série de valores diários do portfólio."""
    try:
        values = (
            PortfolioDailyValue.query.filter_by(portfolio_id=portfolio_id)
            .order_by(PortfolioDailyValue.date)
            .all()
        )

        result = [
            {
                "date": v.date.isoformat(),
                "total_value": float(v.total_value),
                "total_cost": float(v.total_cost),
                "total_gain": float(v.total_gain),
                "total_gain_percent": float(v.total_gain_percent),
            }
            for v in values
        ]

        return jsonify({"success": True, "values": result})
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        return (
            jsonify({"success": False, "error": "Erro ao buscar histórico"}),
            500,
        )


@portfolio_bp.route("/<int:portfolio_id>/daily-contribution", methods=["GET"])
def get_portfolio_daily_contribution(portfolio_id: int):
    """Retorna a contribuição diária por ativo do portfólio."""
    try:
        summary = calculate_portfolio_summary(portfolio_id)
        if not summary:
            return (
                jsonify({"success": False, "error": "Portfólio não encontrado"}),
                404,
            )

        contributions = [
            {"symbol": h["symbol"], "contribution": h["contribution"]}
            for h in summary["holdings"]
        ]
        return jsonify({"success": True, "contributions": contributions})
    except Exception as e:
        logger.error(f"Erro ao calcular contribuição diária: {e}")
        return (
            jsonify({"success": False, "error": "Erro ao calcular contribuição diária"}),
            500,
        )


@portfolio_bp.route("/<int:portfolio_id>/suggested", methods=["GET"])
def get_suggested_portfolio(portfolio_id: int):
    """Retorna a lista de ativos sugeridos para o portfólio."""
    try:
        summary = calculate_portfolio_summary(portfolio_id)
        if not summary:
            return (
                jsonify({"success": False, "error": "Portfólio não encontrado"}),
                404,
            )

        position_pct = {h["symbol"]: h["position_pct"] for h in summary["holdings"]}

        positions = (
            PortfolioPosition.query.filter_by(portfolio_id=portfolio_id)
            .join(Ticker, PortfolioPosition.symbol == Ticker.symbol)
            .join(Company, Ticker.company_id == Company.id, isouter=True)
            .join(
                AssetMetrics,
                PortfolioPosition.symbol == AssetMetrics.symbol,
                isouter=True,
            )
            .all()
        )

        assets = []
        for pos in positions:
            current_price = (
                float(pos.metrics.last_price)
                if pos.metrics and pos.metrics.last_price is not None
                else 0.0
            )
            target_price = current_price * 1.1 if current_price else 0.0
            upside = (
                ((target_price - current_price) / current_price * 100)
                if current_price
                else 0.0
            )
            weight = position_pct.get(pos.symbol, 0.0)

            assets.append(
                {
                    "ticker": pos.symbol,
                    "company": pos.ticker.company.company_name
                    if pos.ticker and pos.ticker.company
                    else "",
                    "currency": "BRL",
                    "currentPrice": current_price,
                    "targetPrice": target_price,
                    "upsideDownside": upside,
                    "mktCap": 0,
                    "pe26": "N/A",
                    "pe5yAvg": "N/A",
                    "deltaPe": "N/A",
                    "evEbitda26": "N/A",
                    "evEbitda5yAvg": "N/A",
                    "deltaEvEbitda": "N/A",
                    "epsGrowth26": "N/A",
                    "ibovWeight": 0,
                    "portfolioWeight": weight,
                    "owUw": weight,
                }
            )

        return jsonify({"success": True, "assets": assets})
    except Exception as e:
        logger.error(f"Erro ao buscar ativos sugeridos: {e}")
        return (
            jsonify({"success": False, "error": "Erro ao buscar ativos sugeridos"}),
            500,
        )


@portfolio_bp.route("/<int:portfolio_id>/sector-weights", methods=["GET"])
def get_portfolio_sector_weights(portfolio_id: int):
    """Retorna os pesos por setor do portfólio."""
    try:
        summary = calculate_portfolio_summary(portfolio_id)
        if not summary:
            return (
                jsonify({"success": False, "error": "Portfólio não encontrado"}),
                404,
            )

        position_pct = {h["symbol"]: h["position_pct"] for h in summary["holdings"]}

        positions = (
            PortfolioPosition.query.filter_by(portfolio_id=portfolio_id)
            .join(
                AssetMetrics,
                PortfolioPosition.symbol == AssetMetrics.symbol,
                isouter=True,
            )
            .all()
        )

        weights = {}
        for pos in positions:
            sector = pos.metrics.sector if pos.metrics and pos.metrics.sector else "Unknown"
            weights[sector] = weights.get(sector, 0.0) + position_pct.get(pos.symbol, 0.0)

        result = [
            {
                "sector": sector,
                "ibovWeight": 0,
                "portfolioWeight": pct,
                "owUw": pct,
            }
            for sector, pct in weights.items()
        ]

        return jsonify({"success": True, "weights": result})
    except Exception as e:
        logger.error(f"Erro ao calcular pesos por setor: {e}")
        return (
            jsonify({"success": False, "error": "Erro ao calcular pesos por setor"}),
            500,
        )


@portfolio_bp.route("/<int:portfolio_id>/editable-metrics", methods=["POST"])
def update_editable_metrics(portfolio_id: int):
    """Atualiza métricas editáveis do portfólio."""
    data = request.get_json(silent=True) or []
    if not isinstance(data, list):
        return jsonify({"success": False, "error": "Formato inválido"}), 400

    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return (
                jsonify({"success": False, "error": "Portfólio não encontrado"}),
                404,
            )

        today = date.today()
        for item in data:
            metric_key = item.get("metric_key") or item.get("metricKey")  # Aceita ambos os formatos
            metric_value = item.get("metric_value") or item.get("metricValue")  # Aceita ambos os formatos
            
            # Validar e converter os valores
            if metric_key is None:
                logger.warning("Chave da métrica ausente no item")
                continue
                
            try:
                # Converter o valor para float
                metric_value = float(metric_value) if metric_value is not None else 0.0
            except (ValueError, TypeError) as e:
                logger.warning(f"Erro ao converter valor da métrica {metric_key}: {e}")
                metric_value = 0.0

            logger.info(f"Processando métrica {metric_key} com valor {metric_value} para data {today}")
            
            record = PortfolioEditableMetric.query.filter_by(
                portfolio_id=portfolio_id, metric_key=metric_key, date=today
            ).first()

            if record:
                record.metric_value = metric_value
                record.updated_at = func.now()
                logger.info(f"Atualizando métrica {metric_key} com valor {metric_value}")
            else:
                new_metric = PortfolioEditableMetric(
                    portfolio_id=portfolio_id,
                    metric_key=metric_key,
                    metric_value=metric_value,
                    date=today,
                )
                db.session.add(new_metric)
                logger.info(f"Criando nova métrica {metric_key} com valor {metric_value}")
                
        # Log para verificar as métricas antes de salvar
        metrics = PortfolioEditableMetric.query.filter_by(portfolio_id=portfolio_id, date=today).all()
        logger.info(f"Métricas antes do commit para portfolio {portfolio_id} na data {today}:")
        for metric in metrics:
            logger.info(f"  {metric.metric_key}: {metric.metric_value} (ID: {metric.id})")

        db.session.commit()
        logger.info(f"Métricas editáveis atualizadas com sucesso para o portfólio {portfolio_id}")
        
        # Verificar as métricas após o commit
        metrics_after = PortfolioEditableMetric.query.filter_by(portfolio_id=portfolio_id, date=today).all()
        logger.info(f"Métricas após commit para portfolio {portfolio_id} na data {today}:")
        for metric in metrics_after:
            logger.info(f"  {metric.metric_key}: {metric.metric_value} (ID: {metric.id})")
        
        return jsonify({"success": True}), 201
    except Exception as e:
        db.session.rollback()
        logger.error("Erro ao salvar métricas editáveis", exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro ao salvar métricas editáveis",
                    "detail": str(e),
                }
            ),
            500,
        )


@portfolio_bp.route("/<int:portfolio_id>/editable-metrics", methods=["GET"])
def get_editable_metrics(portfolio_id: int):
    """Retorna as métricas editáveis do portfólio para a data atual ou a data mais recente disponível."""
    try:
        today = date.today()
        logger.info(f"Buscando métricas editáveis para portfolio {portfolio_id} na data {today}")
        
        # Primeiro tentar buscar métricas para a data atual
        metrics = PortfolioEditableMetric.query.filter_by(
            portfolio_id=portfolio_id, date=today
        ).all()
        
        # Se não encontrar métricas para a data atual, buscar a data mais recente disponível
        if not metrics:
            logger.info(f"Não encontradas métricas para {today}, buscando data mais recente...")
            latest_metric = PortfolioEditableMetric.query.filter_by(
                portfolio_id=portfolio_id
            ).order_by(PortfolioEditableMetric.date.desc()).first()
            
            if latest_metric:
                latest_date = latest_metric.date
                logger.info(f"Encontrada data mais recente: {latest_date}")
                metrics = PortfolioEditableMetric.query.filter_by(
                    portfolio_id=portfolio_id, date=latest_date
                ).all()
            else:
                logger.info("Nenhuma métrica encontrada no banco de dados")
                metrics = []
        else:
            logger.info(f"Encontradas {len(metrics)} métricas no banco de dados para a data {today}")

        result = []
        for m in metrics:
            try:
                metric_value = float(m.metric_value) if m.metric_value is not None else 0.0
                result.append({
                    "metric_key": m.metric_key,
                    "metric_value": metric_value
                })
                logger.info(f"Métrica encontrada: {m.metric_key} = {metric_value}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Erro ao converter valor da métrica {m.metric_key}: {e}")
                result.append({
                    "metric_key": m.metric_key,
                    "metric_value": 0.0
                })

        logger.info(f"Retornando {len(result)} métricas: {result}")
        return jsonify({"success": True, "metrics": result})
    except Exception as e:
        logger.error(f"Erro ao buscar métricas editáveis: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return (
            jsonify({"success": False, "error": "Erro ao buscar métricas editáveis", "details": str(e)}),
            500,
        )
