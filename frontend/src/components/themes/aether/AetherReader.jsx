import React, { useState, useEffect } from 'react';
import api from '@/services/apiClient';
import { Eye, MessageSquare, ArrowRight, X, Sparkles, BookOpen } from 'lucide-react';

export function AetherReader({ projectId }) {
    const [chapters, setChapters] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedChapter, setSelectedChapter] = useState(null);
    const [reviewing, setReviewing] = useState({});
    const [reviewData, setReviewData] = useState({});

    useEffect(() => {
        if (projectId) {
            setLoading(true);
            api.get(`/projects/${projectId}/chapters`, { params: { sort_by: 'order', order: 'asc' } })
                .then(res => setChapters(res.data))
                .catch(err => console.error(err))
                .finally(() => setLoading(false));
        }
    }, [projectId]);

    const requestReview = async (chapterId) => {
        setReviewing(prev => ({ ...prev, [chapterId]: true }));
        try {
            const res = await api.post(`/translation/chapters/${chapterId}/review`);
            if (res.data.review_available) {
                setReviewData(prev => ({ ...prev, [chapterId]: res.data.review_text }));
            }
        } catch (e) {
            console.error(e);
        } finally {
            setReviewing(prev => ({ ...prev, [chapterId]: false }));
        }
    };

    const translatedChapters = chapters.filter(ch => ch.translated_text);

    if (loading) return <div className="text-center py-12 text-slate-500 animate-pulse">Summoning scrolls...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-accent/10 rounded-xl">
                    <BookOpen className="w-5 h-5 text-accent" />
                </div>
                <h3 className="text-xl font-heading font-bold text-slate-800">Translated Scriptures</h3>
            </div>

            {translatedChapters.length === 0 ? (
                <div className="text-center py-12 border border-white/40 bg-white/20 rounded-3xl text-slate-500 italic">
                    No translations found in the ether. Translate chapters first.
                </div>
            ) : (
                <div className="grid gap-4">
                    {translatedChapters.map((chapter, idx) => (
                        <div
                            key={chapter.id}
                            onClick={() => setSelectedChapter(chapter)}
                            className="group cursor-pointer bg-white/40 backdrop-blur-sm border border-white/50 rounded-2xl p-5 shadow-sm hover:shadow-lg hover:shadow-accent/10 hover:-translate-y-1 transition-all duration-300 relative overflow-hidden"
                            style={{ animationDelay: `${idx * 50}ms` }}
                        >
                            <div className="absolute inset-0 bg-gradient-to-r from-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                            <div className="relative z-10 flex justify-between items-center">
                                <div>
                                    <h4 className="font-heading font-bold text-slate-800 group-hover:text-accent transition-colors">{chapter.title}</h4>
                                    <div className="text-xs font-medium text-slate-500 mt-1 flex items-center gap-2">
                                        <span className="bg-white/50 px-2 py-0.5 rounded-full border border-white/30">
                                            Original: {(chapter.original_text || '').length}
                                        </span>
                                        <ArrowRight className="w-3 h-3 opacity-50" />
                                        <span className="bg-accent/10 text-accent px-2 py-0.5 rounded-full border border-accent/20">
                                            Translated: {(chapter.translated_text || '').length}
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-500 mt-3 line-clamp-1 italic opacity-80 font-serif">
                                        "{(chapter.translated_text || '').substring(0, 80)}..."
                                    </p>
                                </div>
                                <div className=" bg-white/50 p-2 rounded-full shadow-sm group-hover:bg-accent group-hover:text-white transition-colors">
                                    <Eye className="w-4 h-4" />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Suspended Reader Modal */}
            {selectedChapter && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div
                        className="absolute inset-0 bg-slate-900/30 backdrop-blur-sm transition-opacity"
                        onClick={() => setSelectedChapter(null)}
                    />

                    <div className="relative w-full max-w-6xl h-[85vh] bg-white/60 backdrop-blur-xl border border-white/60 rounded-[2rem] shadow-2xl overflow-hidden flex flex-col animate-fade-in-up">
                        {/* Modal Header */}
                        <div className="flex items-center justify-between px-8 py-5 border-b border-white/30 bg-white/20">
                            <div>
                                <h2 className="text-xl font-heading font-bold text-slate-800 flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-accent" />
                                    {selectedChapter.title}
                                </h2>
                            </div>
                            <button
                                onClick={() => setSelectedChapter(null)}
                                className="p-2 hover:bg-white/40 rounded-full transition-colors"
                            >
                                <X className="w-5 h-5 text-slate-600" />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="flex-1 overflow-hidden flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x divide-white/30">
                            {/* Original */}
                            <div className="flex-1 flex flex-col min-h-0 bg-white/10">
                                <div className="px-6 py-3 text-xs font-bold uppercase tracking-widest text-slate-400">Source Text</div>
                                <div className="flex-1 overflow-y-auto px-8 pb-8 custom-scrollbar-glass">
                                    <div className="font-serif text-slate-600 leading-relaxed whitespace-pre-wrap text-sm">
                                        {selectedChapter.original_text}
                                    </div>
                                </div>
                            </div>

                            {/* Translation */}
                            <div className="flex-1 flex flex-col min-h-0 bg-white/30">
                                <div className="px-6 py-3 text-xs font-bold uppercase tracking-widest text-accent">Target Text</div>
                                <div className="flex-1 overflow-y-auto px-8 pb-8 custom-scrollbar-glass">
                                    <div className="font-serif text-slate-800 leading-loose whitespace-pre-wrap text-base drop-shadow-sm">
                                        {selectedChapter.translated_text}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Modal Footer */}
                        <div className="p-4 border-t border-white/30 bg-white/20 flex justify-end gap-3">
                            {reviewData[selectedChapter.id] ? (
                                <div className="flex-1 bg-yellow-50/50 border border-yellow-200/50 rounded-xl p-3 text-sm text-yellow-800 overflow-y-auto max-h-24">
                                    <strong className="flex items-center gap-2 mb-1"><Sparkles className="w-3 h-3" /> AI Analysis</strong>
                                    {reviewData[selectedChapter.id]}
                                </div>
                            ) : (
                                <button
                                    onClick={() => requestReview(selectedChapter.id)}
                                    disabled={reviewing[selectedChapter.id]}
                                    className="px-5 py-2.5 rounded-xl bg-accent text-white font-bold shadow-lg hover:shadow-accent/30 hover:-translate-y-0.5 transition-all text-sm flex items-center gap-2 disabled:opacity-50"
                                >
                                    {reviewing[selectedChapter.id] ? (
                                        <span className="animate-pulse">Divining...</span>
                                    ) : (
                                        <>
                                            <MessageSquare className="w-4 h-4" />
                                            Request Analysis
                                        </>
                                    )}
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
