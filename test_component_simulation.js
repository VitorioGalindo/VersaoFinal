// Simulando o que acontece no componente PortfolioDashboard
let portfolio = null;
let error = null;

// Função para simular o carregamento dos dados
const loadSummary = async () => {
  try {
    // Simulando a resposta da API
    const data = {
      "success": true,
      "summary": {
        "exposicao_total_pct": 102.01889176582117,
        "id": 1,
        "name": "Portfolio 1",
        "net_long_pct": 73.401580231963,
        "patrimonio_liquido": 10312747.99,
        "posicao_comprada_pct": 87.71023599889209,
        "posicao_vendida_pct": 14.308655766929098,
        "valor_cota": 119.03811425075605,
        "variacao_cota_pct": 4.584531937055059
      }
    };
    
    console.log('Portfolio summary loaded:', data);
    console.log('Valor da cota:', data.summary.valor_cota);
    console.log('Variação da cota:', data.summary.variacao_cota_pct);
    console.log('Posição comprada:', data.summary.posicao_comprida_pct);
    console.log('Posição vendida:', data.summary.posicao_vendida_pct);
    console.log('Net long:', data.summary.net_long_pct);
    console.log('Exposição total:', data.summary.exposicao_total_pct);
    
    // Simulando a atualização do estado
    portfolio = data.summary;
    error = null;
    
    console.log('Portfolio state updated:', portfolio);
  } catch (err) {
    console.error(err);
    error = 'Erro ao carregar portfólio';
  }
};

// Funções de formatação
const formatCurrency = (v) => {
  if (v === undefined || v === null) return 'R$ 0.00';
  return `R$ ${v.toFixed(2)}`;
};

const formatPercent = (v) => {
  if (v === undefined || v === null) return '0.00%';
  return `${v.toFixed(2)}%`;
};

// Testando o processo completo
console.log('Iniciando teste de simulação do componente...');
loadSummary().then(() => {
  if (portfolio) {
    console.log('\nValores exibidos no componente:');
    console.log('Patrimônio Líquido:', formatCurrency(portfolio.patrimonio_liquido));
    console.log('Valor da Cota:', `R$ ${portfolio.valor_cota !== undefined && portfolio.valor_cota !== null ? portfolio.valor_cota.toFixed(2) : '0.00'}`);
    console.log('Variação da Cota:', formatPercent(portfolio.variacao_cota_pct));
    console.log('Posição Comprada:', formatPercent(portfolio.posicao_comprada_pct));
    console.log('Posição Vendida:', formatPercent(portfolio.posicao_vendida_pct));
    console.log('Net Long:', formatPercent(portfolio.net_long_pct));
    console.log('Exposição Total:', formatPercent(portfolio.exposicao_total_pct));
  } else {
    console.log('Nenhum dado de portfólio disponível');
  }
  
  if (error) {
    console.log('Erro:', error);
  }
});