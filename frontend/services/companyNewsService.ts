import { CompanyNewsItem } from '../types';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001/api';

const normalizeItem = (item: any): CompanyNewsItem => ({
  id: item.id,
  url: item.url,
  title: item.title,
  summary: item.summary,
  source: item.source,
  publishedDate: item.publishedDate || item.published_date,
});

const list = async (ticker: string): Promise<CompanyNewsItem[]> => {
  const res = await fetch(`${API_BASE}/company-news/${ticker}`);
  if (!res.ok) {
    throw new Error('Falha ao buscar notícias da empresa');
  }
  const json = await res.json();
  const items = (json.news || json.data || json) as any[];
  return items.map(normalizeItem);
};

const create = async (
  data: Omit<CompanyNewsItem, 'id'> & { ticker: string }
): Promise<CompanyNewsItem> => {
  const res = await fetch(`${API_BASE}/company-news`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error('Falha ao criar notícia da empresa');
  }
  const item = await res.json();
  return normalizeItem(item);
};

const update = async (
  id: number,
  data: Partial<Omit<CompanyNewsItem, 'id'>>
): Promise<CompanyNewsItem> => {
  const res = await fetch(`${API_BASE}/company-news/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error('Falha ao atualizar notícia da empresa');
  }
  const item = await res.json();
  return normalizeItem(item);
};

const remove = async (id: number): Promise<void> => {
  const res = await fetch(`${API_BASE}/company-news/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error('Falha ao remover notícia da empresa');
  }
};

export const companyNewsService = {
  list,
  create,
  update,
  remove,
};
