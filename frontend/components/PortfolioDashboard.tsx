import React, { useEffect, useState } from 'react';
import PortfolioManager from './PortfolioManager';
import PortfolioCharts from './PortfolioCharts';
import SuggestedPortfolio from './SuggestedPortfolio';
import SectorWeights from './SectorWeights';
import { PortfolioSummary, SuggestedPortfolioAsset, SectorWeight, EditableMetric } from '../types';
import { portfolioApi } from '../services/portfolioApi';
import { useRealTimeQuotes } from '../services/useRealTimeQuotes';

const PortfolioDashboard: React.FC = () => {
  console.log('PortfolioDashboard rendering');
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [suggested, setSuggested] = useState<SuggestedPortfolioAsset[]>([]);
  const [sectorWeights, setSectorWeights] = useState<SectorWeight[]>([]);
  const [editableMetrics, setEditableMetrics] = useState<EditableMetric[]>([]);

  // Obter os símbolos dos holdings para subscrição em tempo real
  const holdings = portfolio?.holdings ?? [];
  const symbols = holdings.map(h => h.symbol);
  console.log('Portfolio holdings:', holdings);
  console.log('Portfolio symbols:', symbols);
  
  // Usar o hook para obter cotações em tempo real
  const { quotes, connected } = useRealTimeQuotes(symbols);
  console.log('Real-time quotes:', quotes);
  console.log('WebSocket connected:', connected);

  const loadSummary = async () => {
    try {
      // Carregar o resumo do portfólio
      const summaryData = await portfolioApi.getPortfolioSummary(1);
      console.log('Portfolio summary loaded:', summaryData);
      console.log('Valor da cota:', summaryData.valor_cota);
      console.log('Variação da cota:', summaryData.variacao_cota_pct);
      console.log('Posição comprada:', summaryData.posicao_comprada_pct);
      console.log('Posição vendida:', summaryData.posicao_vendida_pct);
      console.log('Net long:', summaryData.net_long_pct);
      console.log('Exposição total:', summaryData.exposicao_total_pct);
      
      // Carregar as holdings do portfólio
      const holdingsData = await portfolioApi.getPortfolioHoldings(1);
      console.log('Portfolio holdings loaded:', holdingsData);
      
      // Combinar os dados do resumo com as holdings
      const combinedData = {
        ...summaryData,
        holdings: holdingsData.holdings
      };
      
      setPortfolio(combinedData);
    } catch (err) {
      console.error(err);
      setError('Erro ao carregar portfólio');
    }
  };

  const loadSuggested = async () => {
    try {
      const data = await portfolioApi.getSuggestedPortfolio(1);
      setSuggested(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadSectorWeights = async () => {
    try {
      const data = await portfolioApi.getSectorWeights(1);
      setSectorWeights(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadEditableMetrics = async () => {
    try {
      const data = await portfolioApi.getEditableMetrics(1);
      setEditableMetrics(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    console.log('Loading portfolio data');
    loadSummary();
    loadSuggested();
    loadSectorWeights();
    loadEditableMetrics();
    
    // Atualizar os dados da carteira a cada 3 segundos
    const interval = setInterval(() => {
      loadSummary();
      loadEditableMetrics();
    }, 3000);
    
    // Limpar o intervalo quando o componente for desmontado
    return () => {
      clearInterval(interval);
    };
  }, []);

  const formatCurrency = (v: number | undefined) => {
    if (v === undefined || v === null) return 'R$ 0.00';
    return `R$ ${v.toFixed(2)}`;
  };
  
  const formatPercent = (v: number | undefined) => {
    if (v === undefined || v === null) return '0.00%';
    return `${v.toFixed(2)}%`;
  };

  // Calcular o valor da linha "Caixa"
  const calculateCashPosition = () => {
    if (!portfolio) return null;
    
    // Obter os valores das métricas editáveis
    const caixaBruto = editableMetrics.find(m => m.metric_key === 'caixaBruto')?.metric_value || 0;
    const outros = editableMetrics.find(m => m.metric_key === 'outros')?.metric_value || 0;
    const outrasDespesas = editableMetrics.find(m => m.metric_key === 'outrasDespesas')?.metric_value || 0;
    
    // Calcular o valor total da caixa
    const cashValue = caixaBruto + outros + outrasDespesas;
    
    // Somente mostrar a linha de caixa se houver valor
    if (cashValue === 0) {
      return null;
    }
    
    return {
      symbol: 'Caixa',
      cashValue
    };
  };

  const cashPosition = calculateCashPosition();
  
  // Calcular o patrimônio líquido corrigido (incluindo caixa)
  const calculateAdjustedNetWorth = () => {
    if (!portfolio) return 0;
    
    // O patrimonio_liquido do backend já inclui o valor das posições e a caixa
    // Não precisamos adicionar a caixa novamente
    return portfolio.patrimonio_liquido;
  };
  
  const adjustedNetWorth = calculateAdjustedNetWorth();
  
  // Recalcular o percentual de cada posição com base no patrimônio líquido ajustado
  const calculatePositionPercent = (positionValue: number) => {
    if (!portfolio) return 0;
    return portfolio.patrimonio_liquido !== 0 ? (positionValue / portfolio.patrimonio_liquido) * 100 : 0;
  };
  
  // Calcular o percentual da caixa com base no patrimônio líquido ajustado
  const cashPercent = cashPosition && portfolio && portfolio.patrimonio_liquido !== 0 ? 
    (cashPosition.cashValue / portfolio.patrimonio_liquido) * 100 : 0;

  return (
    <div className="space-y-6">
      <PortfolioManager
        initialAssets={holdings.map((h, i) => ({
          id: i,
          ticker: h.symbol,
          quantity: h.quantity,
          targetWeight: h.target_pct || 0,
        }))}
        onSaved={() => {
          loadSummary();
          loadEditableMetrics();
        }}
      />

      {error && <p className="text-red-400">{error}</p>}

      {portfolio && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-slate-800/50 rounded-lg p-6 border border-slate-700">
              <h2 className="text-xl font-semibold text-white mb-4">Composição da Carteira</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left text-slate-300 table-auto">
                  <thead className="text-xs text-slate-400 uppercase bg-slate-700/50">
                    <tr>
                      {['ATIVO','COTAÇÃO','VAR. DIA(%)','CONTRIBUIÇÃO(%)','QUANTIDADE','POSIÇÃO(R$)','POSIÇÃO(%)','POSIÇÃO %-ALVO','DIFERENÇA','AJUSTE'].map(h => (
                        <th key={h} className="px-4 py-3 whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {holdings.map(h => {
                      console.log('Rendering holding:', h);
                      // Usar preço em tempo real se disponível, senão usar o preço do portfolio
                      const realTimeQuote = quotes[h.symbol];
                      console.log('Real-time quote for', h.symbol, ':', realTimeQuote);
                      const currentPrice = realTimeQuote ? realTimeQuote.last : h.last_price;
                      const priceChangePercent = realTimeQuote ? realTimeQuote.price_change_percent : h.daily_change_pct;
                      console.log('Current price for', h.symbol, ':', currentPrice);
                      console.log('Price change percent for', h.symbol, ':', priceChangePercent);
                      
                      // Garantir que os valores sejam números válidos
                      const validCurrentPrice = typeof currentPrice === 'number' && !isNaN(currentPrice) ? currentPrice : 0;
                      const validPriceChangePercent = typeof priceChangePercent === 'number' && !isNaN(priceChangePercent) ? priceChangePercent : 0;
                      
                      // Recalcular valores com base no preço em tempo real
                      const positionValue = h.quantity * validCurrentPrice;
                      const cost = h.quantity * h.avg_price;
                      const gain = positionValue - cost;
                      const gainPercent = cost !== 0 ? ((gain / cost) * 100) : 0;
                      const positionPercent = calculatePositionPercent(positionValue);
                      
                      return (
                        <tr key={h.symbol} className="border-b border-slate-700 hover:bg-slate-700/30">
                          <td className="px-4 py-3 font-medium text-white whitespace-nowrap">{h.symbol}</td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center">
                              <span>{formatCurrency(validCurrentPrice)}</span>
                              {realTimeQuote && (
                                <span className={`ml-2 text-xs ${realTimeQuote.is_realtime ? 'text-green-400' : 'text-yellow-400'}`}>
                                  {connected && realTimeQuote.is_realtime ? '●' : '○'}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className={`px-4 py-3 whitespace-nowrap ${validPriceChangePercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>{formatPercent(validPriceChangePercent)}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{formatPercent(h.contribution)}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{h.quantity}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{formatCurrency(positionValue)}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{formatPercent(positionPercent)}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{formatPercent(h.target_pct)}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{formatPercent(h.difference)}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{h.adjustment_qty}</td>
                        </tr>
                      );
                    })}
                    {/* Linha Caixa */}
                    {cashPosition && cashPosition.cashValue > 0 && (
                      <tr className="border-b border-slate-700 hover:bg-slate-700/30">
                        <td className="px-4 py-3 font-medium text-white whitespace-nowrap">{cashPosition.symbol}</td>
                        <td className="px-4 py-3 whitespace-nowrap">-</td>
                        <td className="px-4 py-3 whitespace-nowrap">-</td>
                        <td className="px-4 py-3 whitespace-nowrap">-</td>
                        <td className="px-4 py-3 whitespace-nowrap">-</td>
                        <td className="px-4 py-3 whitespace-nowrap">{formatCurrency(cashPosition.cashValue)}</td>
                        <td className="px-4 py-3 whitespace-nowrap">{formatPercent(cashPercent)}</td>
                        <td className="px-4 py-3 whitespace-nowrap">-</td>
                        <td className="px-4 py-3 whitespace-nowrap">-</td>
                        <td className="px-4 py-3 whitespace-nowrap">-</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700 h-fit">
              <h2 className="text-xl font-semibold text-white mb-4">Resumo do Portfólio</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Patrimônio Líquido:</span>
                  <span className="font-medium text-white">{formatCurrency(adjustedNetWorth)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Valor da Cota:</span>
                  <span className="font-medium text-white">R$ {portfolio.valor_cota !== undefined && portfolio.valor_cota !== null ? portfolio.valor_cota.toFixed(2) : '0.00'}</span>
                </div>
                <div className={`flex justify-between ${portfolio.variacao_cota_pct !== undefined && portfolio.variacao_cota_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  <span>Variação da Cota:</span>
                  <span>{portfolio.variacao_cota_pct !== undefined ? formatPercent(portfolio.variacao_cota_pct) : '0.00%'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Posição Comprada:</span>
                  <span className="font-medium text-white">{formatPercent(portfolio.posicao_comprada_pct)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Posição Vendida:</span>
                  <span className="font-medium text-white">{formatPercent(portfolio.posicao_vendida_pct)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Net Long:</span>
                  <span className="font-medium text-white">{formatPercent(portfolio.net_long_pct)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Exposição Total:</span>
                  <span className="font-medium text-white">{formatPercent(portfolio.exposicao_total_pct)}</span>
                </div>
              </div>
            </div>
          </div>
          <PortfolioCharts />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SuggestedPortfolio assets={suggested} />
            <SectorWeights weights={sectorWeights} />
          </div>
        </>
      )}
    </div>
  );
};

export default PortfolioDashboard;

