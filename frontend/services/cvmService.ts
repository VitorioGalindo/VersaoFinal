import { CvmDocument, CvmCompany, CvmDocumentType } from '../types';

const base = import.meta.env.VITE_API_URL || 'http://localhost:5001';
const API_BASE_URL = base.endsWith('/api') ? base : `${base}/api`;

const buildError = async (response: Response, defaultMsg: string): Promise<never> => {
    let detail = '';
    try {
        const errorData = await response.json();
        detail = errorData?.message || errorData?.error || '';
    } catch {
        // ignore json parsing errors
    }
    throw new Error(detail ? `${defaultMsg}: ${detail}` : defaultMsg);
};

const getCompanies = async (): Promise<CvmCompany[]> => {
    const response = await fetch(`${API_BASE_URL}/cvm/companies`);
    if (!response.ok) return buildError(response, 'Erro ao buscar empresas');
    const data = await response.json();
    return data.companies || [];
};

const getDocumentTypes = async (): Promise<CvmDocumentType[]> => {
    const response = await fetch(`${API_BASE_URL}/cvm/document-types`);
    if (!response.ok) return buildError(response, 'Erro ao buscar tipos de documento');
    const data = await response.json();
    return (data.document_types || []).map((d: any) =>
        typeof d === 'string'
            ? { code: d, name: d, description: d }
            : d
    );
};

interface DocumentFilter {
    companyId?: number;
    documentType?: string;
    startDate?: string;
    endDate?: string;
    limit?: number;
}

const getDocuments = async (filters: DocumentFilter = {}): Promise<CvmDocument[]> => {
    const params = new URLSearchParams();
    if (filters.documentType) params.append('document_type', filters.documentType);
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.limit) params.append('limit', String(filters.limit));

    let url: string;
    if (filters.companyId) {
        url = `${API_BASE_URL}/documents/by_company/${filters.companyId}?${params.toString()}`;
    } else {
        url = `${API_BASE_URL}/cvm/documents?${params.toString()}`;
    }

    const response = await fetch(url);
    if (!response.ok) return buildError(response, 'Erro ao buscar documentos');
    const data = await response.json();
    const docs = data.documents || [];
    return docs.map((doc: any) => ({
        id: String(doc.id),
        date: doc.delivery_date ? new Date(doc.delivery_date).toLocaleDateString('pt-BR') : '',
        company: doc.company_name || '',
        category: doc.category || doc.document_type || '',
        subject: doc.title || doc.document_subtype || '',
        link: doc.download_url || doc.document_url || '#',
    }));
};

export const cvmService = {
    getCompanies,
    getDocumentTypes,
    getDocuments,
};
