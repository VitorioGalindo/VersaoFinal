import React, { useEffect, useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid, LineChart, Line } from 'recharts';
import { portfolioApi } from '../services/portfolioApi';
import { AssetContribution, PortfolioDailyValue, IbovHistoryPoint } from '../types';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#8dd1e1', '#a4de6c', '#d0ed57'];

const PortfolioCharts: React.FC = () => {
  const [contrib, setContrib] = useState<AssetContribution[]>([]);
  const [dailyValues, setDailyValues] = useState<PortfolioDailyValue[]>([]);
  const [ibov, setIbov] = useState<IbovHistoryPoint[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [c, pv, ib] = await Promise.all([
          portfolioApi.getDailyContribution(1),
          portfolioApi.getPortfolioDailyValues(1),
          portfolioApi.getIbovHistory(),
        ]);
        setContrib(c);
        setDailyValues(pv);
        setIbov(ib);
      } catch (err) {
        console.error('Erro ao carregar gráficos do portfólio', err);
      }
    };
    load();
  }, []);

  const contributionData = useMemo(() => {
    const base: Record<string, number | string> = { name: 'Hoje' };
    contrib.forEach((c) => {
      base[c.symbol] = c.contribution;
    });
    return [base];
  }, [contrib]);

  const lineData = useMemo(() => {
    if (!dailyValues.length || !ibov.length) return [];
    const startPortfolio = dailyValues[0].total_value;
    const ibovStart = ibov[0].close;
    const ibovMap = Object.fromEntries(ibov.map(i => [i.date, i.close]));
    return dailyValues.map(v => {
      const ibClose = ibovMap[v.date];
      return {
        date: v.date,
        portfolio: ((v.total_value / startPortfolio) - 1) * 100,
        ibov: ibClose ? ((ibClose / ibovStart) - 1) * 100 : null,
      };
    });
  }, [dailyValues, ibov]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h2 className="text-xl font-semibold text-white mb-4">Contribuição para Variação Diária</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={contributionData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            {contrib.map((c, idx) => (
              <Bar key={c.symbol} dataKey={c.symbol} stackId="a" fill={COLORS[idx % COLORS.length]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h2 className="text-xl font-semibold text-white mb-4">Retorno Acumulado: Cota vs. Ibovespa</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={lineData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis tickFormatter={(v) => `${v.toFixed(2)}%`} />
            <Tooltip formatter={(v: number) => `${v.toFixed(2)}%`} />
            <Legend />
            <Line type="monotone" dataKey="portfolio" stroke="#8884d8" dot={false} />
            <Line type="monotone" dataKey="ibov" stroke="#82ca9d" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PortfolioCharts;
