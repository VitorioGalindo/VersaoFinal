import React, { useEffect, useState, useCallback } from 'react';
import { CvmDocument, CvmCompany, CvmDocumentType } from '../types';
import { DocumentTextIcon, ChevronDownIcon, ArrowTopRightOnSquareIcon } from '../constants';
import { cvmService } from '../services/cvmService';

interface Option {
    value: string;
    label: string;
}

const FilterDropdown: React.FC<{ label: string; options: Option[]; value: string; onChange: (v: string) => void; className?: string; }> = ({ label, options, value, onChange, className }) => (
    <div>
        <label className="block text-sm font-medium text-slate-400 mb-1">{label}</label>
        <div className="relative">
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className={`w-full appearance-none bg-slate-700 border border-slate-600 rounded-md py-2 px-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 ${className}`}
            >
                {options.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                <ChevronDownIcon />
            </div>
        </div>
    </div>
);

// Função para calcular datas padrão (últimos 7 dias)
const getDefaultDates = () => {
    const today = new Date();
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(today.getDate() - 7);
    
    // Formatar datas como YYYY-MM-DD
    const formatDate = (date: Date) => date.toISOString().split('T')[0];
    
    return {
        startDate: formatDate(sevenDaysAgo),
        endDate: formatDate(today)
    };
};

// Função para abrir documentos da CVM corretamente
const openCvmDocument = (url: string) => {
    // Abrir em uma nova aba com um pequeno atraso para evitar bloqueadores de popup
    const newWindow = window.open('about:blank', '_blank');
    if (newWindow) {
        newWindow.location.href = url;
    }
};

// O filtro utiliza apenas dois campos de data (inicial e final)

const CvmDocuments: React.FC = () => {
    const [companies, setCompanies] = useState<Option[]>([]);
    const [documentTypes, setDocumentTypes] = useState<Option[]>([{ value: '', label: 'Todas' }]);
    const [selectedCompany, setSelectedCompany] = useState<string>('');
    const [selectedDocumentType, setSelectedDocumentType] = useState<string>('');
    const [startDate, setStartDate] = useState<string>('');
    const [endDate, setEndDate] = useState<string>('');
    const [documents, setDocuments] = useState<CvmDocument[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadFilters = async () => {
            try {
                const companyData: CvmCompany[] = await cvmService.getCompanies();
                setCompanies([{ value: '', label: 'Todas' }, ...companyData.map(c => ({ value: String(c.id), label: `${c.ticker} - ${c.company_name}` }))]);
            } catch (e: any) {
                setCompanies([{ value: '', label: 'Todas' }]);
                setError(e?.message ?? 'Erro ao carregar empresas');
            }

            try {
                const docTypes: CvmDocumentType[] = await cvmService.getDocumentTypes();
                setDocumentTypes([{ value: '', label: 'Todas' }, ...docTypes.map(dt => ({ value: dt.code, label: dt.name }))]);
            } catch (e: any) {
                setDocumentTypes([{ value: '', label: 'Todas' }]);
                setError(e?.message ?? 'Erro ao carregar tipos de documento');
            }
        };
        loadFilters();
    }, []);

    // Definir datas padrão (últimos 7 dias) quando o componente montar
    useEffect(() => {
        const { startDate: defaultStart, endDate: defaultEnd } = getDefaultDates();
        setStartDate(defaultStart);
        setEndDate(defaultEnd);
    }, []);

    // Filtros de data manipulados diretamente pelos campos de input

    const fetchDocs = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const docs = await cvmService.getDocuments({
                companyId: selectedCompany ? Number(selectedCompany) : undefined,
                documentType: selectedDocumentType || undefined,
                startDate: startDate || undefined,
                endDate: endDate || undefined,
                limit: 50,
            });
            setDocuments(docs);
        } catch (e: any) {
            setDocuments([]);
            setError(e?.message ?? 'Erro ao carregar documentos');
        } finally {
            setLoading(false);
        }
    }, [selectedCompany, selectedDocumentType, startDate, endDate]);

    useEffect(() => {
        const handler = setTimeout(fetchDocs, 500);
        return () => clearTimeout(handler);
    }, [fetchDocs]);


    return (
        <div className="bg-slate-800/50 rounded-lg p-6 md:p-8 space-y-6 border border-slate-700">
            <div className="flex items-center gap-3">
                <DocumentTextIcon className="w-8 h-8 text-sky-400" />
                <h1 className="text-3xl font-bold text-white">Documentos CVM</h1>
            </div>

            <div className="border-b border-slate-700 pb-6">
                <h2 className="text-xl font-semibold text-white mb-4">Filtros</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <FilterDropdown
                        label="Filtrar por Empresa"
                        options={companies}
                        value={selectedCompany}
                        onChange={setSelectedCompany}
                    />
                    <FilterDropdown
                        label="Filtrar por Categoria"
                        options={documentTypes}
                        value={selectedDocumentType}
                        onChange={setSelectedDocumentType}
                    />
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Filtrar por Período de Publicação</label>

                        <div className="flex gap-2">
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                placeholder="YYYY-MM-DD"
                                className="w-full bg-slate-700 border border-slate-600 rounded-md py-2 px-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                            />
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                placeholder="YYYY-MM-DD"
                                className="w-full bg-slate-700 border border-slate-600 rounded-md py-2 px-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                            />
                        </div>

                    </div>
                </div>
                <div className="flex justify-end mt-4">
                    <button
                        onClick={fetchDocs}
                        disabled={loading}
                        className="bg-sky-600 text-white font-semibold px-4 py-2 rounded-md hover:bg-sky-500 disabled:bg-slate-600 disabled:cursor-not-allowed transition-colors"
                    >
                        {loading ? 'Buscando...' : 'Buscar'}
                    </button>
                </div>
            </div>

            <div>
                {loading ? (
                    <div className="flex justify-center py-10" role="status">
                        <div className="w-8 h-8 border-4 border-sky-400 border-t-transparent rounded-full animate-spin" />
                        <span className="sr-only">Carregando...</span>
                    </div>
                ) : error ? (
                    <p className="text-red-500">{error}</p>
                ) : (
                    <>
                        <p className="text-md font-semibold text-white mb-4">
                            Exibindo {documents.length} documentos encontrados
                        </p>
                        <div className="overflow-x-auto border border-slate-700 rounded-lg">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-slate-700/50 text-xs text-slate-400 uppercase">
                                    <tr>
                                        {['Data', 'Empresa', 'Categoria', 'Assunto', 'Link'].map(h => (
                                            <th key={h} scope="col" className="px-6 py-3 font-medium tracking-wider">{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {documents.map((doc) => (
                                        <tr key={doc.id} className="hover:bg-slate-700/30">
                                            <td className="px-6 py-4 whitespace-nowrap text-slate-300">{doc.date}</td>
                                            <td className="px-6 py-4 whitespace-nowrap font-medium text-white">{doc.company}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-slate-300">{doc.category}</td>
                                            <td className="px-6 py-4 text-slate-300 max-w-xs break-words">{doc.subject}</td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <button 
                                                    onClick={() => openCvmDocument(doc.link)}
                                                    className="flex items-center gap-1 text-sky-400 hover:text-sky-300 font-semibold"
                                                >
                                                    Abrir
                                                    <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default CvmDocuments;
