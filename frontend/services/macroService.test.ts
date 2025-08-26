import { describe, it, expect, beforeEach, vi } from 'vitest';
import { macroService } from './macroService';

describe('macroService', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.unstubAllGlobals();
  });

  it('getIndicators retorna indicadores', async () => {
    const mockIndicators = [{ name: 'Selic', value: '11', change: '0', changeType: 'neutral', historicalData: [] }];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ indicators: mockIndicators })
    }));
    const indicators = await macroService.getIndicators();
    expect(indicators).toEqual(mockIndicators);
  });

  it('getIndicators lança erro quando resposta não ok', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }));
    await expect(macroService.getIndicators()).rejects.toThrow('Falha ao buscar indicadores macroeconômicos');
  });

  it('getHistory retorna histórico', async () => {
    const mockHistory = [{ date: '2024-01-01', value: 10 }];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ history: mockHistory })
    }));
    const history = await macroService.getHistory('selic');
    expect(history).toEqual(mockHistory);
  });

  it('getHistory lança erro quando resposta não ok', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }));
    await expect(macroService.getHistory('selic')).rejects.toThrow('Falha ao buscar histórico macroeconômico');
  });
});

