import { render, screen } from '@testing-library/react';
import MacroData from './MacroData';


describe('MacroData', () => {
  it('renders indicators after fetch', async () => {
    const mockResp = {
      success: true,
      indicators: {
        SELIC: { value: 10.5, unit: '%', description: 'Taxa Selic', updated_at: null }
      }
    };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResp)
    }) as any;

    render(<MacroData />);

    expect(await screen.findByText('SELIC')).toBeInTheDocument();
  });
});
