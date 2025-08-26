import React, { useState, useEffect } from 'react';
import { ResearchNote } from '../types';
import { PlusIcon, MagnifyingGlassIcon, TrashIcon } from '../constants';
import MDEditor from '@uiw/react-md-editor';

const Research: React.FC = () => {
    const [notes, setNotes] = useState<ResearchNote[]>([]);
    const [activeNoteId, setActiveNoteId] = useState<number | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const activeNote = notes.find(note => note.id === activeNoteId);

    useEffect(() => {
        const loadNotes = async () => {
            try {
                const res = await fetch('/api/research/notes');
                if (res.ok) {
                    const { notes } = await res.json();
                    setNotes(notes);
                    if (notes.length > 0) {
                        setActiveNoteId(notes[0].id);
                    }
                } else {
                    console.error('Failed to load notes');
                }
            } catch (err) {
                console.error('Error loading notes', err);
            }
        };

        loadNotes();
    }, []);

    const handleNewNote = async () => {
        try {
            console.log("Iniciando criação de nova nota");
            const res = await fetch('/api/research/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: 'Nova Anotação', content: '' })
            });
            console.log("Resposta recebida:", res);
            if (res.ok) {
                const { note } = await res.json();
                console.log("Nota criada:", note);
                setNotes(prev => [note, ...prev]);
                setActiveNoteId(note.id);
            } else {
                const { error } = await res.json();
                console.error('Erro ao criar nota', error);
                alert(error);
            }
        } catch (err) {
            console.error('Failed to create note', err);
        }
    };

    const handleGenerateCompanyNotes = async () => {
        try {
            setIsGenerating(true);
            const res = await fetch('/api/research/generate-company-notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            
            if (res.ok) {
                const { notes, message } = await res.json();
                // Adicionar as novas notas ao estado existente
                setNotes(prev => [...notes, ...prev]);
                alert(message);
            } else {
                const { error } = await res.json();
                console.error('Erro ao gerar notas', error);
                alert(error);
            }
        } catch (err) {
            console.error('Failed to generate company notes', err);
            alert('Erro ao gerar notas para empresas');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDeleteCompanyNotes = async () => {
        try {
            setIsDeleting(true);
            const res = await fetch('/api/research/delete-company-notes', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
            });
            
            if (res.ok) {
                const { message } = await res.json();
                // Recarregar as notas após a exclusão
                const loadRes = await fetch('/api/research/notes');
                if (loadRes.ok) {
                    const { notes } = await loadRes.json();
                    setNotes(notes);
                    setActiveNoteId(notes[0]?.id ?? null);
                }
                alert(message);
            } else {
                const { error } = await res.json();
                console.error('Erro ao excluir notas', error);
                alert(error);
            }
        } catch (err) {
            console.error('Failed to delete company notes', err);
            alert('Erro ao excluir notas de empresas');
        } finally {
            setIsDeleting(false);
        }
    };

    const handleDeleteNote = async (noteId: number) => {
        try {
            const res = await fetch(`/api/research/notes/${noteId}`, { method: 'DELETE' });
            if (res.ok) {
                setNotes(prevNotes => {
                    const remaining = prevNotes.filter(note => note.id !== noteId);
                    if (activeNoteId === noteId) {
                        setActiveNoteId(remaining[0]?.id ?? null);
                    }
                    return remaining;
                });
            } else {
                const { error } = await res.json();
                console.error('Failed to delete note', error);
                alert(error);
            }
        } catch (err) {
            console.error('Failed to delete note', err);
        }
    };

    const handleUpdateNote = (field: 'title' | 'content', value: string) => {
        if (!activeNoteId) return;
        setNotes(prevNotes => {
            const updated = prevNotes.map(note =>
                note.id === activeNoteId
                    ? { ...note, [field]: value, last_updated: new Date().toISOString() }
                    : note
            );
            const noteToUpdate = updated.find(n => n.id === activeNoteId);
            if (noteToUpdate) {
                fetch(`/api/research/notes/${activeNoteId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(noteToUpdate)
                })
                    .then(async res => {
                        if (!res.ok) {
                            const { error } = await res.json();
                            console.error('Failed to update note', error);
                            alert(error);
                        }
                    })
                    .catch(err => console.error('Failed to update note', err));
            }
            return updated;
        });
    };

    const filteredNotes = notes.filter(note =>
        note.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        note.content.toLowerCase().includes(searchTerm.toLowerCase())
    ).sort((a, b) => 
        new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime()
    );

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('pt-BR', {
            day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    }

    return (
        <div className="flex h-full bg-[#0d1117] rounded-lg border border-slate-700 overflow-hidden">
            {/* Sidebar de Notas */}
            <div className="w-1/3 max-w-sm border-r border-slate-700 flex flex-col bg-[#0d1117]">
                <div className="p-4 border-b border-slate-700 flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white">Pesquisa & Estudos</h2>
                </div>
                <div className="p-4 space-y-4">
                    <button 
                        onClick={handleNewNote} 
                        className="w-full bg-sky-600 text-white font-semibold py-2 rounded-md hover:bg-sky-500 transition-colors flex items-center justify-center gap-2"
                    >
                        <PlusIcon className="w-5 h-5" />
                        Nova Nota
                    </button>
                    <button 
                        onClick={handleGenerateCompanyNotes} 
                        disabled={isGenerating}
                        className={`w-full text-white font-semibold py-2 rounded-md transition-colors flex items-center justify-center gap-2 ${
                            isGenerating 
                                ? 'bg-gray-600 cursor-not-allowed' 
                                : 'bg-green-600 hover:bg-green-500'
                        }`}
                    >
                        {isGenerating ? 'Gerando...' : 'Gerar Notas para Empresas'}
                    </button>
                    <button 
                        onClick={handleDeleteCompanyNotes} 
                        disabled={isDeleting}
                        className={`w-full text-white font-semibold py-2 rounded-md transition-colors flex items-center justify-center gap-2 ${
                            isDeleting 
                                ? 'bg-gray-600 cursor-not-allowed' 
                                : 'bg-red-600 hover:bg-red-500'
                        }`}
                    >
                        {isDeleting ? 'Excluindo...' : 'Excluir Notas de Empresas'}
                    </button>
                    <div className="relative">
                        <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                            <MagnifyingGlassIcon />
                        </div>
                        <input
                            type="text"
                            placeholder="Buscar notas..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-slate-700 border border-slate-600 rounded-md py-2 pl-10 pr-4 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500"
                        />
                    </div>
                </div>
                <div className="flex-grow overflow-y-auto">
                    {filteredNotes.map(note => {
                        const noteDate = new Date(note.last_updated);
                        const now = new Date();
                        const isRecent = (now.getTime() - noteDate.getTime()) / (1000 * 60 * 60) < 24; // Menos de 24 horas
                        
                        return (
                            <div
                                key={note.id}
                                onClick={() => setActiveNoteId(note.id)}
                                className={`p-4 cursor-pointer border-l-4 transition-all duration-200 relative ${
                                    activeNoteId === note.id 
                                        ? 'bg-slate-700/70 border-sky-500 shadow-lg' 
                                        : 'border-transparent hover:bg-slate-700/30'
                                }`}
                            >
                                {isRecent && (
                                    <span className="absolute top-2 right-2 w-2 h-2 bg-green-500 rounded-full"></span>
                                )}
                                <h3 className="font-semibold text-white truncate">{note.title}</h3>
                                <p className="text-sm text-slate-400 truncate mt-1">
                                    {note.content.split('\n')[0] || 'Nenhum conteúdo adicional'}
                                </p>
                                <p className="text-xs text-slate-500 mt-2">{formatDate(note.last_updated)}</p>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Editor Principal */}
            <div className="flex-1 flex flex-col bg-[#0d1117]">
                {activeNote ? (
                    <>
                        <div className="p-4 border-b border-slate-700 flex justify-between items-center">
                            <p className="text-sm text-slate-400">Última atualização: {formatDate(activeNote.last_updated)}</p>
                            <button onClick={() => handleDeleteNote(activeNote.id)} className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded-full">
                                <TrashIcon className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex-grow flex flex-col overflow-y-auto">
                           <input
                                type="text"
                                value={activeNote.title}
                                onChange={(e) => handleUpdateNote('title', e.target.value)}
                                className="w-full p-4 text-2xl font-bold bg-transparent text-white focus:outline-none placeholder-slate-500"
                                placeholder="Título da nota"
                           />
                           <div className="flex-grow w-full">
                               <MDEditor
                                   value={activeNote.content}
                                   onChange={(content) => handleUpdateNote('content', content || '')}
                                   height="100%"
                                   visible={true}
                                   preview="edit"
                                   data-color-mode="dark"
                               />
                           </div>
                       </div>
                   </>
               ) : (
                    <div className="flex items-center justify-center h-full text-center text-slate-500">
                        <div>
                            <h2 className="text-xl font-semibold">Nenhuma nota selecionada</h2>
                            <p>Selecione uma nota da lista ou crie uma nova para começar.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Research;
