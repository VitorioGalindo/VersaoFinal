import React from 'react';
import { SectorWeight } from '../types';

interface Props {
  weights: SectorWeight[];
}

const SectorWeights: React.FC<Props> = ({ weights }) => {
  const formatPercent = (v: number) => `${v.toFixed(2)}%`;

  return (
    <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
      <h2 className="text-xl font-semibold text-white mb-4">Pesos por Setor</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-slate-300">
          <thead className="text-xs text-slate-400 uppercase bg-slate-700/50">
            <tr>
              {['Setor','Peso Ibov','Peso Carteira','OW/UW'].map(h => (
                <th key={h} className="px-4 py-3 whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {weights.map(w => (
              <tr key={w.sector} className="border-b border-slate-700 hover:bg-slate-700/30">
                <td className="px-4 py-3 font-medium text-white whitespace-nowrap">{w.sector}</td>
                <td className="px-4 py-3">{formatPercent(w.ibovWeight)}</td>
                <td className="px-4 py-3">{formatPercent(w.portfolioWeight)}</td>
                <td className={`px-4 py-3 ${w.owUw >= 0 ? 'text-green-400' : 'text-red-400'}`}>{formatPercent(w.owUw)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SectorWeights;
