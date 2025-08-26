import { MacroIndicator } from '../types';

export async function fetchMacroIndicators(): Promise<MacroIndicator[]> {
  const res = await fetch('/api/macro/indicators');
  if (!res.ok) {
    throw new Error('Falha ao buscar indicadores macroeconômicos');
  }
  const data = await res.json();
  if (Array.isArray(data.indicators)) {
    return data.indicators as MacroIndicator[];
  }
  return Object.entries(data.indicators).map(([name, info]: any) => ({
    name,
    value: String(info.value),
    change: '',
    changeType: 'neutral',
    historicalData: [],
  }));
}

export async function getIndicators(): Promise<MacroIndicator[]> {
  return fetchMacroIndicators();
}

export async function getHistory(
  indicator: string,
): Promise<{ date: string; value: number }[]> {
  const res = await fetch(`/api/macro/${indicator}/history`);
  if (!res.ok) {
    throw new Error('Falha ao buscar histórico macroeconômico');
  }
  const data = await res.json();
  return data.history as { date: string; value: number }[];
}

export const macroService = {
  getIndicators,
  getHistory,
};

