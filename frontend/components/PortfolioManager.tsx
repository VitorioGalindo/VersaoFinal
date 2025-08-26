import React, { useEffect, useState } from 'react';
import { EditableAsset, DailyMetric } from '../types';
import { ChevronUpIcon, PencilSquareIcon, TrashIcon, PlusIcon } from '../constants';
import { upsertPositions, updateDailyMetrics, getEditableMetrics, updateEditableMetrics } from '../services/portfolioApi';

interface PortfolioManagerProps {
    initialAssets?: EditableAsset[];
    onSaved?: () => void;
}

const initialMetrics: DailyMetric[] = [
    { id: 'cotaD1', label: 'COTA D-1', value: 0 },
    { id: 'qtdCotas', label: 'Quantidade de Cotas', value: 0 },
    { id: 'caixaBruto', label: 'Caixa Bruto', value: 0 },
    { id: 'outros', label: 'Outros', value: 0 },
    { id: 'outrasDespesas', label: 'Outras Despesas', value: 0 },
];

const PortfolioManager: React.FC<PortfolioManagerProps> = ({ initialAssets = [], onSaved }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [assets, setAssets] = useState<EditableAsset[]>(initialAssets);
    const [metrics, setMetrics] = useState<DailyMetric[]>(initialMetrics);
    const [editableAssets, setEditableAssets] = useState<EditableAsset[]>(initialAssets);
    
    console.log('PortfolioManager renderizado com initialAssets:', initialAssets);

    useEffect(() => {
        console.log('PortfolioManager: initialAssets atualizado', initialAssets);
        // Inicializar os ativos editáveis apenas na primeira vez
        if (editableAssets.length === 0 && initialAssets.length > 0) {
            console.log('Inicializando editableAssets com initialAssets', initialAssets);
            setEditableAssets(initialAssets);
        }
        
        // Atualizar os ativos salvos sempre que initialAssets mudar
        setAssets(initialAssets);
    }, [initialAssets]);

    useEffect(() => {
        // Buscar as métricas editáveis quando o componente for montado
        const fetchEditableMetrics = async () => {
            try {
                console.log('Buscando métricas editáveis...');
                const data = await getEditableMetrics(1);
                console.log('Métricas recebidas do backend:', data);
                
                // Verificar se data é um array
                if (!Array.isArray(data)) {
                    console.error('Dados recebidos não são um array:', data);
                    return;
                }
                
                // Atualizar as métricas com os valores do backend
                const updatedMetrics = initialMetrics.map(metric => {
                    const savedMetric = data.find(m => m.metric_key === metric.id);
                    const updatedMetric = savedMetric ? { ...metric, value: savedMetric.metric_value } : metric;
                    return updatedMetric;
                });
                setMetrics(updatedMetrics);
            } catch (error) {
                console.error('Erro ao buscar métricas editáveis:', error);
            }
        };

        // Buscar as métricas editáveis quando o componente for montado
        fetchEditableMetrics();
    }, []);

    const handleAssetChange = (id: number, field: keyof EditableAsset, value: string | number) => {
        setEditableAssets(editableAssets.map(asset => asset.id === id ? { ...asset, [field]: value } : asset));
    };
    
    const handleAddAsset = () => {
        const newId = editableAssets.length > 0 ? Math.max(...editableAssets.map(a => a.id)) + 1 : 1;
        setEditableAssets([...editableAssets, { id: newId, ticker: '', quantity: 0, targetWeight: 0 }]);
    };

    const handleDeleteAsset = (id: number) => {
        setEditableAssets(editableAssets.filter(asset => asset.id !== id));
    };

    const handleMetricChange = (id: string, newValue: number) => {
        setMetrics(metrics.map(metric => metric.id === id ? { ...metric, value: newValue } : metric));
    };
    
    const adjustMetric = (id: string, amount: number) => {
        const metric = metrics.find(m => m.id === id);
        if (metric) {
            let precision = 0;
            // Handle precision for decimal values
            if (metric.label.includes('Cota')) {
                precision = 4;
            } else if (String(metric.value).includes('.')) {
                precision = 2;
            }
            const newValue = parseFloat((metric.value + amount).toFixed(precision));
            handleMetricChange(id, newValue);
        }
    };

    const handleSavePortfolio = async () => {
        try {
            // Salvar as posições usando a API
            await upsertPositions(1, editableAssets.map(asset => ({
                symbol: asset.ticker,
                quantity: asset.quantity,
                target_weight: asset.targetWeight
            })));
            
            // Atualizar o estado assets após salvar com sucesso
            setAssets(editableAssets);
            
            // Chamar callback de sucesso
            onSaved?.();
            
            alert('Carteira salva com sucesso!');
        } catch (error) {
            console.error(error);
            alert('Erro ao salvar carteira');
        }
    };

    const handleUpdateMetrics = async () => {
        try {
            await updateEditableMetrics(
                1,
                metrics.map(m => ({ metric_key: m.id, metric_value: m.value })),
            );
            onSaved?.();
            alert('Métricas atualizadas com sucesso!');
        } catch (error) {
            console.error(error);
            alert('Erro ao atualizar métricas');
        }
    };
    
    if (!isOpen) {
        return (
            <div className="bg-slate-800/50 rounded-lg p-2 border border-slate-700">
                <button onClick={() => setIsOpen(true)} className="w-full flex justify-between items-center px-4 py-2 text-white">
                    <div className="flex items-center gap-2">
                        <PencilSquareIcon />
                        <span className="font-semibold">Gerenciar Ativos e Métricas</span>
                    </div>
                    <ChevronUpIcon />
                </button>
            </div>
        )
    }

    return (
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
            <button onClick={() => setIsOpen(false)} className="w-full flex justify-between items-center mb-4 text-white">
                 <div className="flex items-center gap-2">
                    <PencilSquareIcon />
                    <span className="font-semibold">Gerenciar Ativos e Métrica</span>
                </div>
                <ChevronUpIcon className="w-5 h-5 transform rotate-180" />
            </button>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Gerenciar Ativos da Carteira */}
                <div>
                    <h3 className="text-lg font-semibold text-white mb-2">Gerenciar Ativos da Carteira</h3>
                    <div className="bg-sky-900/50 text-sky-200 text-sm p-3 rounded-md mb-4 border border-sky-800">
                        Adicione, edite ou remova linhas. Depois, clique em 'Salvar Carteira'.
                    </div>
                    <div className="max-h-96 overflow-y-auto pr-2">
                        <table className="w-full text-sm text-left text-slate-300">
                             <thead className="text-xs text-slate-400 uppercase bg-slate-700/50 sticky top-0">
                                <tr>
                                    <th className="px-3 py-2">Ticker</th>
                                    <th className="px-3 py-2">Quantidade</th>
                                    <th className="px-3 py-2">% Alvo</th>
                                    <th className="px-3 py-2"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {editableAssets.map(asset => (
                                    <tr key={asset.id} className="border-b border-slate-700">
                                        <td className="p-1">
                                            <input type="text" value={asset.ticker} onChange={e => handleAssetChange(asset.id, 'ticker', e.target.value.toUpperCase())} className="w-full bg-slate-600 rounded-md p-2 border border-slate-500 focus:ring-sky-500 focus:border-sky-500"/>
                                        </td>
                                        <td className="p-1">
                                            <input type="number" value={asset.quantity} onChange={e => handleAssetChange(asset.id, 'quantity', Number(e.target.value))} className="w-full bg-slate-600 rounded-md p-2 border border-slate-500 focus:ring-sky-500 focus:border-sky-500"/>
                                        </td>
                                        <td className="p-1">
                                            <input type="number" value={asset.targetWeight} onChange={e => handleAssetChange(asset.id, 'targetWeight', Number(e.target.value))} className="w-full bg-slate-600 rounded-md p-2 border border-slate-500 focus:ring-sky-500 focus:border-sky-500"/>
                                        </td>
                                        <td className="p-1 text-center">
                                            <button onClick={() => handleDeleteAsset(asset.id)} className="p-2 text-slate-400 hover:text-red-400"><TrashIcon /></button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                     <div className="flex justify-between items-center mt-4">
                        <button onClick={handleAddAsset} className="flex items-center gap-1 text-sm text-sky-400 hover:text-sky-300">
                           <PlusIcon className="w-4 h-4" /> Adicionar Ativo
                        </button>
                        <button onClick={handleSavePortfolio} className="bg-sky-600 text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-sky-500">
                            Salvar Carteira
                        </button>
                    </div>
                </div>

                {/* Editar Métricas Diárias */}
                <div>
                     <h3 className="text-lg font-semibold text-white mb-2">Editar Métricas Diárias</h3>
                     <div className="bg-slate-700/50 p-4 rounded-lg space-y-3">
                        {metrics.map(metric => (
                             <div key={metric.id}>
                                <label className="text-sm text-slate-400">{metric.label}</label>
                                <div className="flex items-center gap-2 mt-1">
                                    <button onClick={() => adjustMetric(metric.id, -1)} className="px-2 py-1 bg-slate-600 rounded-md hover:bg-slate-500">-</button>
                                    <input 
                                      type="number"
                                      value={metric.value}
                                      onChange={e => handleMetricChange(metric.id, Number(e.target.value))}
                                      className="w-full text-center bg-slate-800 rounded-md p-2 border border-slate-600 focus:ring-sky-500 focus:border-sky-500"
                                    />
                                    <button onClick={() => adjustMetric(metric.id, 1)} className="px-2 py-1 bg-slate-600 rounded-md hover:bg-slate-500">+</button>
                                </div>
                             </div>
                        ))}
                         <button onClick={handleUpdateMetrics} className="w-full bg-slate-600 text-white mt-4 px-4 py-2 rounded-md text-sm font-semibold hover:bg-slate-500">
                            Atualizar Métricas
                        </button>
                     </div>
                </div>
            </div>
        </div>
    )
}

export default PortfolioManager;
