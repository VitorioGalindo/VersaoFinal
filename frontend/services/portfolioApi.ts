import {
  PortfolioSummary,
  PortfolioDailyValue,
  AssetContribution,
  IbovHistoryPoint,
  SuggestedPortfolioAsset,
  SectorWeight,
  Asset,
} from '../types';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001/api';

export async function getPortfolioSummary(id: number): Promise<PortfolioSummary> {
  const res = await fetch(`${API_BASE}/portfolio-summary/${id}/summary`);
  if (!res.ok) {
    throw new Error('Falha ao buscar portfólio');
  }
  const data = await res.json();
  return data.summary as PortfolioSummary;
}

export async function getPortfolioHoldings(id: number): Promise<{id: number, name: string, holdings: Asset[]}> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/summary`);
  if (!res.ok) {
    throw new Error('Falha ao buscar holdings do portfólio');
  }
  const data = await res.json();
  return data.portfolio as {id: number, name: string, holdings: Asset[]};
}

export async function savePortfolioSnapshot(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/snapshot`, { method: 'POST' });
  if (!res.ok) {
    throw new Error('Falha ao salvar snapshot');
  }
}

export async function upsertPositions(
  id: number,
  positions: { symbol: string; quantity: number; avg_price?: number; target_weight?: number }[],
): Promise<void> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/positions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(positions),
  });
  if (!res.ok) {
    throw new Error('Falha ao salvar posições');
  }
}

export async function getPortfolioDailyValues(id: number): Promise<PortfolioDailyValue[]> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/daily-values`);
  if (!res.ok) {
    throw new Error('Falha ao buscar histórico do portfólio');
  }
  const data = await res.json();
  return data.values as PortfolioDailyValue[];
}

export async function getDailyContribution(id: number): Promise<AssetContribution[]> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/daily-contribution`);
  if (!res.ok) {
    throw new Error('Falha ao buscar contribuição diária');
  }
  const data = await res.json();
  return data.contributions as AssetContribution[];
}

export async function getSuggestedPortfolio(id: number): Promise<SuggestedPortfolioAsset[]> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/suggested`);
  if (!res.ok) {
    throw new Error('Falha ao buscar carteira sugerida');
  }
  const data = await res.json();
  return data.assets as SuggestedPortfolioAsset[];
}

export async function getSectorWeights(id: number): Promise<SectorWeight[]> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/sector-weights`);
  if (!res.ok) {
    throw new Error('Falha ao buscar pesos por setor');
  }
  const data = await res.json();
  return data.weights as SectorWeight[];
}

export async function getIbovHistory(): Promise<IbovHistoryPoint[]> {
  const res = await fetch(`${API_BASE}/market/ibov-history`);
  if (!res.ok) {
    throw new Error('Falha ao buscar histórico do Ibovespa');
  }
  const data = await res.json();
  return data.history as IbovHistoryPoint[];
}

export async function updateDailyMetrics(
  id: number,
  metrics: { id: string; value: number }[],
): Promise<void> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/daily-metrics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metrics),
  });
  if (!res.ok) {
    throw new Error('Falha ao atualizar métricas');
  }
}

export async function getEditableMetrics(
  id: number,
): Promise<{ metric_key: string; metric_value: number }[]> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/editable-metrics`);
  if (!res.ok) {
    throw new Error('Falha ao buscar métricas editáveis');
  }
  const data = await res.json();
  return data.metrics as { metric_key: string; metric_value: number }[];
}

export async function updateEditableMetrics(
  id: number,
  metrics: { metric_key: string; metric_value: number }[],
): Promise<void> {
  const res = await fetch(`${API_BASE}/portfolio/${id}/editable-metrics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metrics),
  });
  if (!res.ok) {
    throw new Error('Falha ao atualizar métricas editáveis');
  }
}
export const portfolioApi = {
  getPortfolioSummary,
  getPortfolioHoldings,
  savePortfolioSnapshot,
  upsertPositions,
  getPortfolioDailyValues,
  getDailyContribution,
  getIbovHistory,
  updateDailyMetrics,
  getEditableMetrics,
  updateEditableMetrics,
  getSuggestedPortfolio,
  getSectorWeights,
};

