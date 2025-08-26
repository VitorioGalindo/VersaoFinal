import React from 'react';
import { SuggestedPortfolioAsset } from '../types';

interface Props {
  assets: SuggestedPortfolioAsset[];
}

const SuggestedPortfolio: React.FC<Props> = ({ assets }) => {
  const formatCurrency = (v: number) => `R$ ${v.toFixed(2)}`;
  const formatPercent = (v: number) => `${v.toFixed(2)}%`;

  return (
    <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
      <h2 className="text-xl font-semibold text-white mb-4">Carteira Sugerida</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-slate-300">
          <thead className="text-xs text-slate-400 uppercase bg-slate-700/50">
            <tr>
              {['Ticker','Empresa','Preço Atual','Preço-Alvo','Upside','Peso Ibov','Peso Carteira','OW/UW'].map(h => (
                <th key={h} className="px-4 py-3 whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {assets.map(a => (
              <tr key={a.ticker} className="border-b border-slate-700 hover:bg-slate-700/30">
                <td className="px-4 py-3 font-medium text-white whitespace-nowrap">{a.ticker}</td>
                <td className="px-4 py-3">{a.company}</td>
                <td className="px-4 py-3">{formatCurrency(a.currentPrice)}</td>
                <td className="px-4 py-3">{formatCurrency(a.targetPrice)}</td>
                <td className={`px-4 py-3 ${a.upsideDownside >= 0 ? 'text-green-400' : 'text-red-400'}`}>{formatPercent(a.upsideDownside)}</td>
                <td className="px-4 py-3">{formatPercent(a.ibovWeight)}</td>
                <td className="px-4 py-3">{formatPercent(a.portfolioWeight)}</td>
                <td className={`px-4 py-3 ${a.owUw >= 0 ? 'text-green-400' : 'text-red-400'}`}>{formatPercent(a.owUw)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SuggestedPortfolio;
