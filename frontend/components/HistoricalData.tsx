
import React, { useState, useEffect, useRef } from 'react';
import { FinancialHistoryRow, CvmCompany } from '../types';
import { InformationCircleIcon, ChevronUpIcon } from '../constants';

// Adicionando ícone de gráfico (vamos usar um SVG simples por enquanto)
const ChartIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
    <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
  </svg>
);

// Componente de gráfico de linha simples
const LineChart = ({ data }: { data: { period: string; value: number }[] }) => {
  if (data.length === 0) return null;

  // Encontrar valores mínimo e máximo para escala
  const values = data.map(d => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = maxValue - minValue || 1; // Evitar divisão por zero

  // Dimensões do gráfico
  const width = 800;
  const height = 400;
  const padding = 60;

  // Calcular pontos
  const points = data.map((d, i) => {
    const x = padding + (i * (width - 2 * padding) / (data.length - 1));
    // Corrigir o cálculo do Y para que valores maiores fiquem mais acima
    const y = padding + ((maxValue - d.value) / range) * (height - 2 * padding);
    return { x, y, ...d };
  });

  // Gerar path para a linha
  const pathData = points.map((p, i) => 
    `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
  ).join(' ');

  // Gerar grades verticais
  const gridLines = [];
  for (let i = 0; i <= 5; i++) {
    const y = padding + (i * (height - 2 * padding) / 5);
    // Corrigir o cálculo do valor para corresponder à posição Y
    const value = maxValue - (i * range / 5);
    gridLines.push({ y, value });
  }

  return (
    <div className="relative overflow-x-auto">
      <svg width={width} height={height} className="overflow-visible">
        {/* Grade horizontal */}
        {gridLines.map((line, i) => (
          <g key={i}>
            <line 
              x1={padding} 
              y1={line.y} 
              x2={width - padding} 
              y2={line.y} 
              stroke="#334155" 
              strokeWidth="1" 
            />
            <text 
              x={padding - 10} 
              y={line.y + 4} 
              textAnchor="end" 
              fill="#94a3b8" 
              fontSize="12"
            >
              {line.value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </text>
          </g>
        ))}
        
        {/* Grade vertical */}
        {points.map((point, i) => (
          <line 
            key={i}
            x1={point.x} 
            y1={padding} 
            x2={point.x} 
            y2={height - padding} 
            stroke="#334155" 
            strokeWidth="1" 
            strokeDasharray="2,2"
          />
        ))}
        
        {/* Eixo X */}
        <line 
          x1={padding} 
          y1={height - padding} 
          x2={width - padding} 
          y2={height - padding} 
          stroke="#64748b" 
          strokeWidth="2" 
        />
        
        {/* Eixo Y */}
        <line 
          x1={padding} 
          y1={padding} 
          x2={padding} 
          y2={height - padding} 
          stroke="#64748b" 
          strokeWidth="2" 
        />
        
        {/* Linha do gráfico */}
        <path 
          d={pathData} 
          fill="none" 
          stroke="#38bdf8" 
          strokeWidth="3" 
        />
        
        {/* Pontos de dados */}
        {points.map((point, i) => (
          <g key={i}>
            <circle 
              cx={point.x} 
              cy={point.y} 
              r="6" 
              fill="#38bdf8" 
              className="hover:r-8 transition-all cursor-pointer"
            />
            {/* Tooltip ao passar o mouse */}
            <text 
              x={point.x} 
              y={point.y - 15} 
              textAnchor="middle" 
              fill="white" 
              fontSize="14"
              className="opacity-0 hover:opacity-100 transition-opacity font-bold"
            >
              {point.value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </text>
          </g>
        ))}
        
        {/* Rótulos de período */}
        {points.map((point, i) => (
          <text 
            key={i}
            x={point.x} 
            y={height - padding + 25} 
            textAnchor="middle" 
            fill="#cbd5e1" 
            fontSize="14"
            fontWeight="500"
          >
            {point.period}
          </text>
        ))}
        
        {/* Título do eixo Y */}
        <text 
          x={20} 
          y={height / 2} 
          textAnchor="middle" 
          fill="#cbd5e1" 
          fontSize="14"
          fontWeight="500"
          transform={`rotate(-90, 20, ${height / 2})`}
        >
          Valores
        </text>
      </svg>
    </div>
  );
};


const HistoricalData: React.FC<{ ticker: string }> = ({ ticker }) => {
    const [rows, setRows] = useState<FinancialHistoryRow[]>([]);
    const [balanceSheetAssetRows, setBalanceSheetAssetRows] = useState<FinancialHistoryRow[]>([]);
    const [balanceSheetLiabilityRows, setBalanceSheetLiabilityRows] = useState<FinancialHistoryRow[]>([]);
    const [incomeStatementRows, setIncomeStatementRows] = useState<FinancialHistoryRow[]>([]);
    const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
    const [companies, setCompanies] = useState<CvmCompany[]>([]);
    const [filteredCompanies, setFilteredCompanies] = useState<CvmCompany[]>([]);
    const [selectedTicker, setSelectedTicker] = useState<string>(ticker || 'PRIO3');
    const [selectedCompanyName, setSelectedCompanyName] = useState<string>('');
    const [loadingCompanies, setLoadingCompanies] = useState<boolean>(true);
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
    const [reportType, setReportType] = useState<'annual' | 'quarterly'>('annual');
    const [isChartModalOpen, setIsChartModalOpen] = useState<boolean>(false);
    const [chartData, setChartData] = useState<{ period: string; value: number }[]>([]);
    const [chartTitle, setChartTitle] = useState<string>('');
    const [scrollBarPosition, setScrollBarPosition] = useState<'top' | 'bottom'>('bottom');
    const [horizontalScrollPositions, setHorizontalScrollPositions] = useState({
        incomeStatement: 0,
        balanceSheetAsset: 0,
        balanceSheetLiability: 0
    });
    const [activeTable, setActiveTable] = useState<'incomeStatement' | 'balanceSheetAsset' | 'balanceSheetLiability' | null>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const tableRefs = {
        incomeStatement: useRef<HTMLDivElement>(null),
        balanceSheetAsset: useRef<HTMLDivElement>(null),
        balanceSheetLiability: useRef<HTMLDivElement>(null)
    };
    const scrollBarRef = useRef<HTMLDivElement>(null);

    // Fechar dropdown ao clicar fora
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsDropdownOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // Monitorar posição de rolagem para mover a barra de rolagem
    useEffect(() => {
        const handleScroll = () => {
            const scrollTop = window.scrollY;
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            
            // Se estiver próximo do topo, posicionar a barra no topo
            if (scrollTop < 100) {
                setScrollBarPosition('top');
            } 
            // Se estiver próximo do final, posicionar a barra no final
            else if (scrollTop + windowHeight > documentHeight - 100) {
                setScrollBarPosition('bottom');
            }
        };

        window.addEventListener('scroll', handleScroll);
        // Chamar uma vez para definir a posição inicial
        handleScroll();
        return () => {
            window.removeEventListener('scroll', handleScroll);
        };
    }, []);

    // Monitorar rolagem horizontal das tabelas
    useEffect(() => {
        const tables = [
            { ref: tableRefs.incomeStatement, key: 'incomeStatement' as const },
            { ref: tableRefs.balanceSheetAsset, key: 'balanceSheetAsset' as const },
            { ref: tableRefs.balanceSheetLiability, key: 'balanceSheetLiability' as const }
        ];

        const handleHorizontalScroll = (e: Event) => {
            const target = e.target as HTMLDivElement;
            const tableKey = Object.keys(tableRefs).find(
                key => tableRefs[key as keyof typeof tableRefs].current === target
            ) as keyof typeof tableRefs | undefined;
            
            if (tableKey) {
                setHorizontalScrollPositions(prev => ({
                    ...prev,
                    [tableKey]: target.scrollLeft
                }));
                setActiveTable(tableKey);
            }
        };

        // Adicionar listeners de rolagem
        tables.forEach(({ ref }) => {
            if (ref.current) {
                ref.current.addEventListener('scroll', handleHorizontalScroll);
            }
        });

        return () => {
            tables.forEach(({ ref }) => {
                if (ref.current) {
                    ref.current.removeEventListener('scroll', handleHorizontalScroll);
                }
            });
        };
    }, []);

    // Buscar lista de empresas
    useEffect(() => {
        const fetchCompanies = async () => {
            try {
                setLoadingCompanies(true);
                const res = await fetch('/api/cvm/companies?limit=1000');
                const json = await res.json();
                if (json.companies) {
                    // Ordenar empresas por nome
                    const sortedCompanies = json.companies.sort((a: CvmCompany, b: CvmCompany) => 
                        a.company_name.localeCompare(b.company_name)
                    );
                    setCompanies(sortedCompanies);
                    setFilteredCompanies(sortedCompanies);
                    
                    // Definir o nome da empresa selecionada inicialmente
                    const selectedCompany = sortedCompanies.find(company => company.ticker === selectedTicker);
                    if (selectedCompany) {
                        setSelectedCompanyName(selectedCompany.company_name);
                    }
                }
            } catch (err) {
                console.error('Erro ao buscar empresas', err);
            } finally {
                setLoadingCompanies(false);
            }
        };
        fetchCompanies();
    }, []);

    // Filtrar empresas com base no termo de busca
    useEffect(() => {
        if (searchTerm.trim() === '') {
            setFilteredCompanies(companies);
        } else {
            const filtered = companies.filter(company => 
                company.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
                company.company_name.toLowerCase().includes(searchTerm.toLowerCase())
            );
            setFilteredCompanies(filtered);
        }
    }, [searchTerm, companies]);

    // Buscar dados históricos quando o ticker selecionado ou tipo de relatório mudar
    useEffect(() => {
        const fetchData = async () => {
            try {
                const reportTypeParam = reportType === 'annual' ? 'DFP' : 'ITR';
                const res = await fetch(`/api/financials/history/${selectedTicker}?report_type=${reportTypeParam}`);
                const json = await res.json();
                if (json.success) {
                    // Separar dados por tipo de demonstração (BPA, BPP, DRE)
                    const bpaData = json.data.filter((item: any) => 
                        item.report_version === 'BPA_CON' || item.report_version === 'BPA_IND'
                    );
                    const bppData = json.data.filter((item: any) => 
                        item.report_version === 'BPP_CON' || item.report_version === 'BPP_IND'
                    );
                    const dreData = json.data.filter((item: any) => 
                        item.report_version === 'DRE_CON' || item.report_version === 'DRE_IND'
                    );

                    // Função para agrupar dados por conta
                    const groupDataByAccount = (data: any[], includeTTM: boolean = false) => {
                        // Primeiro tentar usar dados CONSOLIDADOS, se não houver, usar INDIVIDUAIS
                        const consolidatedData = data.filter(item => item.report_version.includes('CON'));
                        const individualData = data.filter(item => item.report_version.includes('IND'));
                        
                        // Usar dados consolidados se disponíveis, senão usar individuais
                        const dataToUse = consolidatedData.length > 0 ? consolidatedData : individualData;
                        
                        const grouped: { [code: string]: FinancialHistoryRow } = {};
                        dataToUse.forEach((item: any) => {
                            if (!item.reference_date) return;
                            
                            // Formatar período (ano ou trimestre)
                            let period;
                            if (reportType === 'annual') {
                                period = new Date(item.reference_date).getFullYear().toString();
                            } else {
                                const date = new Date(item.reference_date);
                                const year = date.getFullYear();
                                const month = date.getMonth();
                                let quarter;
                                if (month < 3) quarter = '1T';
                                else if (month < 6) quarter = '2T';
                                else if (month < 9) quarter = '3T';
                                else quarter = '4T';
                                period = `${quarter}-${year}`;
                            }
                            
                            if (!grouped[item.account_code]) {
                                grouped[item.account_code] = { 
                                    id: item.account_code, 
                                    metric: item.account_name, 
                                    level: 1, 
                                    data: {} 
                                };
                            }
                            grouped[item.account_code].data[period] = { value: Number(item.account_value) };
                        });
                        
                        // Converter para array e ordenar por account_code
                        return Object.values(grouped).sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }));
                    };

                    // Agrupar dados para cada tipo de demonstração
                    const bpaRows = groupDataByAccount(bpaData);
                    const bppRows = groupDataByAccount(bppData);
                    const dreRows = groupDataByAccount(dreData);

                    // Se for DRE e dados anuais, calcular TTM
                    let dreRowsWithTTM = dreRows;
                    if (reportType === 'annual') {
                        // Para calcular TTM, precisamos buscar dados trimestrais
                        // Vamos buscar os dados trimestrais separadamente
                        try {
                            const quarterlyRes = await fetch(`/api/financials/history/${selectedTicker}?report_type=ITR`);
                            const quarterlyJson = await quarterlyRes.json();
                            if (quarterlyJson.success) {
                                const quarterlyDreData = quarterlyJson.data.filter((item: any) => 
                                    item.report_version === 'DRE_CON' || item.report_version === 'DRE_IND'
                                );
                                
                                // Primeiro tentar usar dados CONSOLIDADOS, se não houver, usar INDIVIDUAIS
                                const consolidatedQuarterlyData = quarterlyDreData.filter(item => item.report_version.includes('CON'));
                                const individualQuarterlyData = quarterlyDreData.filter(item => item.report_version.includes('IND'));
                                const quarterlyDataToUse = consolidatedQuarterlyData.length > 0 ? consolidatedQuarterlyData : individualQuarterlyData;
                                
                                // Agrupar dados trimestrais por conta
                                const quarterlyGrouped: { [code: string]: { [period: string]: number } } = {};
                                quarterlyDataToUse.forEach((item: any) => {
                                    if (!item.reference_date) return;
                                    
                                    const date = new Date(item.reference_date);
                                    const year = date.getFullYear();
                                    const month = date.getMonth();
                                    let quarter;
                                    if (month < 3) quarter = '1T';
                                    else if (month < 6) quarter = '2T';
                                    else if (month < 9) quarter = '3T';
                                    else quarter = '4T';
                                    const period = `${quarter}-${year}`;
                                    
                                    if (!quarterlyGrouped[item.account_code]) {
                                        quarterlyGrouped[item.account_code] = {};
                                    }
                                    quarterlyGrouped[item.account_code][period] = Number(item.account_value);
                                });
                                
                                // Calcular TTM para cada conta
                                dreRowsWithTTM = dreRows.map(row => {
                                    const newRow = { ...row };
                                    
                                    // Encontrar os 4 últimos trimestres disponíveis
                                    const periods = Object.keys(quarterlyGrouped[row.id] || {}).sort((a, b) => {
                                        const [quarterA, yearA] = a.split('-');
                                        const [quarterB, yearB] = b.split('-');
                                        const yearDiff = parseInt(yearA) - parseInt(yearB);
                                        if (yearDiff !== 0) return yearDiff;
                                        
                                        const quarterOrder: { [key: string]: number } = { '1T': 1, '2T': 2, '3T': 3, '4T': 4 };
                                        return (quarterOrder[quarterA] || 0) - (quarterOrder[quarterB] || 0);
                                    });
                                    
                                    // Pegar os 4 últimos períodos
                                    const lastFourPeriods = periods.slice(-4);
                                    
                                    if (lastFourPeriods.length === 4) {
                                        // Calcular soma dos 4 últimos trimestres
                                        const ttmValue = lastFourPeriods.reduce((sum, period) => {
                                            return sum + (quarterlyGrouped[row.id][period] || 0);
                                        }, 0);
                                        
                                        newRow.data['TTM'] = { value: ttmValue };
                                    }
                                    
                                    return newRow;
                                });
                            }
                        } catch (error) {
                            console.error('Erro ao buscar dados trimestrais para TTM:', error);
                        }
                    }

                    setBalanceSheetAssetRows(bpaRows);
                    setBalanceSheetLiabilityRows(bppRows);
                    setIncomeStatementRows(dreRowsWithTTM);
                }
            } catch (err) {
                console.error('Erro ao buscar histórico financeiro', err);
            }
        };
        fetchData();
    }, [selectedTicker, reportType]);

    const getPeriods = (rows: FinancialHistoryRow[], includeTTM: boolean = false) => {
        const set = new Set<string>();
        rows.forEach(row => Object.keys(row.data).forEach(period => set.add(period)));
        
        // Adicionar TTM se necessário
        if (includeTTM && reportType === 'annual' && !set.has('TTM')) {
            set.add('TTM');
        }
        
        return Array.from(set).sort((a, b) => {
            // Ordenar períodos corretamente (ano ou trimestre-ano)
            if (reportType === 'annual') {
                // Colocar TTM no final, se existir
                if (a === 'TTM') return 1;
                if (b === 'TTM') return -1;
                return parseInt(a) - parseInt(b);
            } else {
                // Para trimestres, ordenar por ano e depois por trimestre
                const [quarterA, yearA] = a.split('-');
                const [quarterB, yearB] = b.split('-');
                const yearDiff = parseInt(yearA) - parseInt(yearB);
                if (yearDiff !== 0) return yearDiff;
                
                const quarterOrder: { [key: string]: number } = { '1T': 1, '2T': 2, '3T': 3, '4T': 4 };
                return (quarterOrder[quarterA] || 0) - (quarterOrder[quarterB] || 0);
            }
        });
    };

    const balanceSheetAssetPeriods = getPeriods(balanceSheetAssetRows);
    const balanceSheetLiabilityPeriods = getPeriods(balanceSheetLiabilityRows);
    const incomeStatementPeriods = getPeriods(incomeStatementRows, true); // Incluir TTM para DRE

    const toggleRow = (rowId: string) => {
        setExpandedRows(prev => {
            const newSet = new Set(prev);
            if (newSet.has(rowId)) {
                newSet.delete(rowId);
            } else {
                newSet.add(rowId);
            }
            return newSet;
        });
    };

    // Função para rolar horizontalmente as tabelas
    const scrollToTableHorizontal = (tableKey: 'incomeStatement' | 'balanceSheetAsset' | 'balanceSheetLiability', direction: 'left' | 'right') => {
        const tableRefsMap = {
            incomeStatement: tableRefs.incomeStatement,
            balanceSheetAsset: tableRefs.balanceSheetAsset,
            balanceSheetLiability: tableRefs.balanceSheetLiability
        };
        
        const tableRef = tableRefsMap[tableKey];
        if (tableRef.current) {
            const scrollAmount = 300;
            const newScrollLeft = tableRef.current.scrollLeft + (direction === 'right' ? scrollAmount : -scrollAmount);
            tableRef.current.scrollTo({ left: newScrollLeft, behavior: 'smooth' });
        }
    };

    const openChartModal = (row: FinancialHistoryRow, tableName: string) => {
        // Preparar dados para o gráfico
        const chartData = Object.entries(row.data)
            .filter(([period, data]) => data.value !== null && data.value !== undefined)
            .map(([period, data]) => ({
                period,
                value: data.value as number
            }))
            .sort((a, b) => {
                // Ordenar períodos corretamente
                if (reportType === 'annual') {
                    if (a.period === 'TTM') return 1;
                    if (b.period === 'TTM') return -1;
                    return parseInt(a.period) - parseInt(b.period);
                } else {
                    const [quarterA, yearA] = a.period.split('-');
                    const [quarterB, yearB] = b.period.split('-');
                    const yearDiff = parseInt(yearA) - parseInt(yearB);
                    if (yearDiff !== 0) return yearDiff;
                    
                    const quarterOrder: { [key: string]: number } = { '1T': 1, '2T': 2, '3T': 3, '4T': 4 };
                    return (quarterOrder[quarterA] || 0) - (quarterOrder[quarterB] || 0);
                }
            });
        
        setChartTitle(`${row.metric} - ${tableName}`);
        setChartData(chartData);
        setIsChartModalOpen(true);
    };

    const renderRow = (row: FinancialHistoryRow, periods: string[], tableName: string) => {
        const isExpanded = expandedRows.has(row.id);

        const formatValue = (value: any) => {
            if (value === null || value === undefined) return '-';
            if (typeof value === 'number') {
                 if (Number.isInteger(value)) return value.toLocaleString('pt-BR');
                 return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
            return value;
        }

        return (
            <React.Fragment key={row.id}>
                <tr className="border-b border-slate-700/50 hover:bg-slate-800/60">
                    <td className="px-4 py-2.5 text-sm font-medium text-white whitespace-nowrap bg-slate-800/80 backdrop-blur-sm sticky left-0 z-10" style={{ paddingLeft: `${row.level * 1.5}rem` }}>
                        <div className="flex items-center gap-2">
                           {row.subRows && (
                                <button onClick={() => toggleRow(row.id)} className="text-slate-400 hover:text-white">
                                    <ChevronUpIcon className={`w-4 h-4 transition-transform ${isExpanded ? '' : 'transform rotate-180'}`} />
                                </button>
                            )}
                            <span className={!row.subRows ? 'pl-6' : ''}>{row.metric}</span>
                            <button 
                                onClick={() => openChartModal(row, tableName)}
                                className="text-slate-400 hover:text-sky-400 cursor-pointer ml-2"
                                title="Ver gráfico"
                            >
                                <ChartIcon />
                            </button>
                            <InformationCircleIcon className="w-4 h-4 text-slate-500 hover:text-sky-400 cursor-pointer ml-1" />
                        </div>
                    </td>
                    {periods.map(period => (
                        <td key={period} className="px-4 py-2.5 text-sm text-right text-slate-200 whitespace-nowrap">
                            {formatValue(row.data[period]?.value)}
                        </td>
                    ))}
                </tr>
                {isExpanded && row.subRows && row.subRows.map(subRow => renderRow(subRow, periods, tableName))}
            </React.Fragment>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-start">
                <div className="flex-1">
                    <h1 className="text-2xl font-bold text-white mb-2">{selectedTicker} - {selectedCompanyName}</h1>
                    <div className="flex items-center gap-4 mb-2">
                        {loadingCompanies ? (
                            <div className="text-white">Carregando empresas...</div>
                        ) : (
                            <div ref={dropdownRef} className="relative w-full">
                                <input
                                    type="text"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    onFocus={() => setIsDropdownOpen(true)}
                                    placeholder="Digite o ticker ou nome da empresa..."
                                    className="w-full bg-slate-800 border border-slate-700 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                                />
                                {isDropdownOpen && (
                                    <div className="absolute z-10 w-full mt-1 bg-slate-800 border border-slate-700 rounded-md max-h-60 overflow-y-auto">
                                        {filteredCompanies.length > 0 ? (
                                            filteredCompanies.map(company => (
                                                <div
                                                    key={company.id}
                                                    className="px-3 py-2 hover:bg-slate-700 cursor-pointer"
                                                    onClick={() => {
                                                        setSelectedTicker(company.ticker);
                                                        setSelectedCompanyName(company.company_name);
                                                        setSearchTerm('');
                                                        setIsDropdownOpen(false);
                                                    }}
                                                >
                                                    {company.ticker} - {company.company_name}
                                                </div>
                                            ))
                                        ) : (
                                            <div className="px-3 py-2 text-slate-400">
                                                Nenhuma empresa encontrada
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                    <p className="text-sm text-slate-400">{selectedCompanyName || 'Dados Históricos'}</p>
                </div>
                <div className="flex items-center gap-2">
                     <button className="px-4 py-2 text-sm font-semibold text-white bg-slate-700/50 border border-slate-600 rounded-md hover:bg-slate-700">Adicione a watchlist</button>
                     <button className="px-4 py-2 text-sm font-semibold text-white bg-sky-600 rounded-md hover:bg-sky-500">Visão Geral</button>
                </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 text-center">
                 <div><p className="text-sm text-slate-400">Valor de Ação</p><p className="text-xl font-bold text-white">R$ 42,66</p></div>
                 <div><p className="text-sm text-slate-400">LPA</p><p className="text-xl font-bold text-white">12,94</p></div>
                 <div><p className="text-sm text-slate-400">VPA</p><p className="text-xl font-bold text-white">29,66</p></div>
            </div>

            {/* Botões para selecionar entre dados anuais e trimestrais */}
            <div className="flex items-center gap-2 mb-4">
                <span className="text-sm font-semibold text-white">Tipo de Dados:</span>
                <button 
                    className={`px-3 py-1.5 text-xs font-semibold rounded-md ${
                        reportType === 'annual' 
                            ? 'text-white bg-sky-600' 
                            : 'text-slate-200 bg-slate-700 hover:bg-slate-600'
                    }`}
                    onClick={() => setReportType('annual')}
                >
                    Anuais
                </button>
                <button 
                    className={`px-3 py-1.5 text-xs font-semibold rounded-md ${
                        reportType === 'quarterly' 
                            ? 'text-white bg-sky-600' 
                            : 'text-slate-200 bg-slate-700 hover:bg-slate-600'
                    }`}
                    onClick={() => setReportType('quarterly')}
                >
                    Trimestrais
                </button>
            </div>

            {/* Tipos de análise */}
            {/* Tabela de Demonstração de Resultados */}
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 mb-8" ref={tableRefs.incomeStatement}>
                <h2 className="text-lg font-bold text-white mb-4">Demonstração de Resultados</h2>
                <div className="relative">
                    <button 
                        onClick={() => scrollToTableHorizontal('incomeStatement', 'left')}
                        className="absolute left-0 top-1/2 transform -translate-y-1/2 z-10 bg-slate-800/80 border border-slate-700 rounded-r-lg p-2 text-white hover:bg-slate-700"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                    </button>
                    <button 
                        onClick={() => scrollToTableHorizontal('incomeStatement', 'right')}
                        className="absolute right-0 top-1/2 transform -translate-y-1/2 z-10 bg-slate-800/80 border border-slate-700 rounded-l-lg p-2 text-white hover:bg-slate-700"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                    </button>
                    <div className="overflow-x-auto border border-slate-700 rounded-lg">
                        <div className="min-w-full inline-block">
                            <table className="w-full text-sm text-left text-slate-300">
                                <thead className="text-xs text-slate-400 uppercase bg-slate-700/50 sticky top-0 z-20">
                                    <tr>
                                        <th scope="col" className="px-4 py-3 font-medium whitespace-nowrap bg-slate-800/80 backdrop-blur-sm sticky left-0 z-10">Conta</th>
                                        {incomeStatementPeriods.map(period => (
                                            <th key={period} scope="col" className="px-4 py-3 font-medium text-right whitespace-nowrap">{period}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700/50">
                                    {incomeStatementRows.map(row => renderRow(row, incomeStatementPeriods, 'Demonstração de Resultados'))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabela de Balanço Patrimonial Ativo */}
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 mb-8" ref={tableRefs.balanceSheetAsset}>
                <h2 className="text-lg font-bold text-white mb-4">Balanço Patrimonial Ativo</h2>
                <div className="relative">
                    <button 
                        onClick={() => scrollToTableHorizontal('balanceSheetAsset', 'left')}
                        className="absolute left-0 top-1/2 transform -translate-y-1/2 z-10 bg-slate-800/80 border border-slate-700 rounded-r-lg p-2 text-white hover:bg-slate-700"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                    </button>
                    <button 
                        onClick={() => scrollToTableHorizontal('balanceSheetAsset', 'right')}
                        className="absolute right-0 top-1/2 transform -translate-y-1/2 z-10 bg-slate-800/80 border border-slate-700 rounded-l-lg p-2 text-white hover:bg-slate-700"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                    </button>
                    <div className="overflow-x-auto border border-slate-700 rounded-lg">
                        <div className="min-w-full inline-block">
                            <table className="w-full text-sm text-left text-slate-300">
                                <thead className="text-xs text-slate-400 uppercase bg-slate-700/50 sticky top-0 z-20">
                                    <tr>
                                        <th scope="col" className="px-4 py-3 font-medium whitespace-nowrap bg-slate-800/80 backdrop-blur-sm sticky left-0 z-10">Conta</th>
                                        {balanceSheetAssetPeriods.map(period => (
                                            <th key={period} scope="col" className="px-4 py-3 font-medium text-right whitespace-nowrap">{period}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700/50">
                                    {balanceSheetAssetRows.map(row => renderRow(row, balanceSheetAssetPeriods, 'Balanço Patrimonial Ativo'))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabela de Balanço Patrimonial Passivo */}
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700" ref={tableRefs.balanceSheetLiability}>
                <h2 className="text-lg font-bold text-white mb-4">Balanço Patrimonial Passivo</h2>
                <div className="relative">
                    <button 
                        onClick={() => scrollToTableHorizontal('balanceSheetLiability', 'left')}
                        className="absolute left-0 top-1/2 transform -translate-y-1/2 z-10 bg-slate-800/80 border border-slate-700 rounded-r-lg p-2 text-white hover:bg-slate-700"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                    </button>
                    <button 
                        onClick={() => scrollToTableHorizontal('balanceSheetLiability', 'right')}
                        className="absolute right-0 top-1/2 transform -translate-y-1/2 z-10 bg-slate-800/80 border border-slate-700 rounded-l-lg p-2 text-white hover:bg-slate-700"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                    </button>
                    <div className="overflow-x-auto border border-slate-700 rounded-lg">
                        <div className="min-w-full inline-block">
                            <table className="w-full text-sm text-left text-slate-300">
                                <thead className="text-xs text-slate-400 uppercase bg-slate-700/50 sticky top-0 z-20">
                                    <tr>
                                        <th scope="col" className="px-4 py-3 font-medium whitespace-nowrap bg-slate-800/80 backdrop-blur-sm sticky left-0 z-10">Conta</th>
                                        {balanceSheetLiabilityPeriods.map(period => (
                                            <th key={period} scope="col" className="px-4 py-3 font-medium text-right whitespace-nowrap">{period}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700/50">
                                    {balanceSheetLiabilityRows.map(row => renderRow(row, balanceSheetLiabilityPeriods, 'Balanço Patrimonial Passivo'))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            {/* Barra de rolagem horizontal móvel */}
            {activeTable && (
                <div className="fixed top-16 left-0 right-0 bg-slate-800/90 backdrop-blur-sm border-b border-slate-700 p-2 z-40">
                    <div className="flex justify-between items-center max-w-7xl mx-auto">
                        <span className="text-sm font-semibold text-slate-200">
                            {activeTable === 'incomeStatement' && 'Demonstração de Resultados'}
                            {activeTable === 'balanceSheetAsset' && 'Balanço Patrimonial Ativo'}
                            {activeTable === 'balanceSheetLiability' && 'Balanço Patrimonial Passivo'}
                        </span>
                        <div className="flex gap-2">
                            <button 
                                onClick={() => scrollToTableHorizontal(activeTable, 'left')}
                                className="p-2 text-slate-200 bg-slate-700 rounded-md hover:bg-slate-600 transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                            </button>
                            <button 
                                onClick={() => scrollToTableHorizontal(activeTable, 'right')}
                                className="p-2 text-slate-200 bg-slate-700 rounded-md hover:bg-slate-600 transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Barra de rolagem horizontal móvel */}
            {activeTable && (
                <div className="fixed top-16 left-0 right-0 bg-slate-800/90 backdrop-blur-sm border-b border-slate-700 p-2 z-40">
                    <div className="flex justify-between items-center max-w-7xl mx-auto">
                        <span className="text-sm font-semibold text-slate-200">
                            {activeTable === 'incomeStatement' && 'Demonstração de Resultados'}
                            {activeTable === 'balanceSheetAsset' && 'Balanço Patrimonial Ativo'}
                            {activeTable === 'balanceSheetLiability' && 'Balanço Patrimonial Passivo'}
                        </span>
                        <div className="flex gap-2">
                            <button 
                                onClick={() => scrollToTableHorizontal(activeTable, 'left')}
                                className="p-2 text-slate-200 bg-slate-700 rounded-md hover:bg-slate-600 transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                            </button>
                            <button 
                                onClick={() => scrollToTableHorizontal(activeTable, 'right')}
                                className="p-2 text-slate-200 bg-slate-700 rounded-md hover:bg-slate-600 transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Gráfico */}
            {isChartModalOpen && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-800 border border-slate-700 rounded-lg w-full max-w-6xl max-h-[90vh] overflow-auto">
                        <div className="p-6 border-b border-slate-700 flex justify-between items-center">
                            <h3 className="text-xl font-bold text-white">{chartTitle}</h3>
                            <button 
                                onClick={() => setIsChartModalOpen(false)}
                                className="text-slate-400 hover:text-white"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <div className="p-6">
                            {chartData.length > 0 ? (
                                <div className="space-y-6">
                                    <LineChart data={chartData} />
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        {chartData.map((data, index) => (
                                            <div key={index} className="bg-slate-700/50 p-4 rounded-md">
                                                <p className="text-sm text-slate-400">{data.period}</p>
                                                <p className="text-xl font-semibold text-white">
                                                    {typeof data.value === 'number' ? data.value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : data.value}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <p className="text-slate-400 text-center py-8">Nenhum dado disponível para exibir</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default HistoricalData;
