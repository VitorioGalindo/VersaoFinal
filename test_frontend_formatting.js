// Teste para verificar o formato dos dados recebidos pelo frontend
const testPortfolioData = {
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

// Funções de formatação do frontend
const formatCurrency = (v) => {
  if (v === undefined || v === null) return 'R$ 0.00';
  return `R$ ${v.toFixed(2)}`;
};

const formatPercent = (v) => {
  if (v === undefined || v === null) return '0.00%';
  return `${v.toFixed(2)}%`;
};

// Testando a formatação
console.log("Testando formatação dos dados:");
console.log("Patrimônio Líquido:", formatCurrency(testPortfolioData.summary.patrimonio_liquido));
console.log("Valor da Cota:", `R$ ${testPortfolioData.summary.valor_cota !== undefined && testPortfolioData.summary.valor_cota !== null ? testPortfolioData.summary.valor_cota.toFixed(2) : '0.00'}`);
console.log("Variação da Cota:", formatPercent(testPortfolioData.summary.variacao_cota_pct));
console.log("Posição Comprada:", formatPercent(testPortfolioData.summary.posicao_comprada_pct));
console.log("Posição Vendida:", formatPercent(testPortfolioData.summary.posicao_vendida_pct));
console.log("Net Long:", formatPercent(testPortfolioData.summary.net_long_pct));
console.log("Exposição Total:", formatPercent(testPortfolioData.summary.exposicao_total_pct));