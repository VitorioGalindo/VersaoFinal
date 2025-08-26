import { StockGuideData } from '../types';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001/api';

const CACHE_KEY = 'stockGuideData';
const CACHE_TTL = 1000 * 60 * 60; // 1 hora

export async function getStockGuideData(): Promise<StockGuideData[]> {
  const cached = typeof window !== 'undefined' ? localStorage.getItem(CACHE_KEY) : null;
  if (cached) {
    try {
      const parsed = JSON.parse(cached) as { timestamp: number; data: StockGuideData[] };
      if (Date.now() - parsed.timestamp < CACHE_TTL) {
        return parsed.data;
      }
    } catch {
      // ignore parse errors and fetch fresh data
    }
  }

  const res = await fetch(`${API_BASE}/market/stock-guide`);
  if (!res.ok) {
    throw new Error('Falha ao buscar dados do stock guide');
  }
  const json = await res.json();
  const result = (json.stockGuide || json.data || json) as StockGuideData[];
  if (typeof window !== 'undefined') {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ timestamp: Date.now(), data: result }));
  }
  return result;
}

export const stockGuideService = { getStockGuideData };

