import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, CheckCircle2, ChevronRight, Play, RefreshCw, XCircle } from 'lucide-react';
import api from '@/services/apiClient';

export function AiReviewPanel({ chapterId, onCorrectionStarted }) {
  const [loading, setLoading] = useState(false);
  const [reviewData, setReviewData] = useState(null);
  const [correcting, setCorrecting] = useState(false);
  const [error, setError] = useState(null);

  const fetchReview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/translation/chapters/${chapterId}/review`);
      if (res.data && res.data.review_available) {
        // Parse the review text if it's JSON from Gemini
        try {
           const parsed = JSON.parse(res.data.review_text);
           setReviewData(parsed);
        } catch (e) {
           setReviewData({ 
             score: null, 
             passed: false, 
             raw: res.data.review_text 
           });
        }
      } else {
        setReviewData(null);
      }
    } catch (err) {
      console.error('Error fetching review', err);
    } finally {
      setLoading(false);
    }
  };

  const runReview = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.post(`/translation/chapters/${chapterId}/review`);
      await fetchReview();
    } catch (err) {
      setError('Failed to run AI QA review.');
      setLoading(false);
    }
  };

  const runCorrection = async () => {
    setCorrecting(true);
    setError(null);
    try {
      if (onCorrectionStarted) onCorrectionStarted();
      await api.post(`/translation/chapters/${chapterId}/translate-with-review?max_retries=1`);
      await fetchReview();
    } catch (err) {
      setError('Failed to apply AI correction.');
    } finally {
      setCorrecting(false);
    }
  };

  useEffect(() => {
    if (chapterId) fetchReview();
  }, [chapterId]);

  if (loading) {
    return (
      <div className="border border-accent/20 bg-surface/50 p-4 text-center animate-pulse flex flex-col items-center">
        <Activity className="w-6 h-6 text-accent mb-2" />
        <span className="text-[10px] text-accent tracking-widest font-mono uppercase">RUNNING_QA_DIAGNOSTICS...</span>
      </div>
    );
  }

  return (
    <div className="border border-accent/30 bg-surface/40 p-0 font-mono text-xs overflow-hidden relative group">
      {/* Header */}
      <div className="bg-accent/10 p-3 border-b border-accent/20 flex justify-between items-center">
        <h3 className="font-bold text-accent flex items-center tracking-widest uppercase">
          <ChevronRight className="w-4 h-4 mr-1 text-secondary-accent" />
          AI_QA_AUDIT_LOG
        </h3>
        {!reviewData && (
          <button 
             onClick={runReview}
             className="px-3 py-1 bg-accent text-bg hover:bg-secondary-accent text-[9px] font-bold tracking-widest flex items-center transition-colors"
          >
            <Play className="w-3 h-3 mr-1" /> RUN_AUDIT
          </button>
        )}
      </div>

      {error && (
        <div className="p-2 bg-destructive/10 text-destructive border-b border-destructive/20 text-[10px] flex items-center">
          <AlertTriangle className="w-3 h-3 mr-2" /> {error}
        </div>
      )}

      {/* Body */}
      <div className="p-4 space-y-4">
        {!reviewData ? (
          <div className="text-muted-foreground text-center py-6 border border-dashed border-accent/20 opacity-50">
            <span className="tracking-widest uppercase text-[10px]">NO_AUDIT_DATA_AVAILABLE. INITIALIZE SCAN.</span>
          </div>
        ) : reviewData.raw ? (
           <div className="whitespace-pre-wrap text-[10px] text-muted-foreground">{reviewData.raw}</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div className="border border-accent/20 p-3 bg-surface/60">
                <div className="text-[10px] text-muted-foreground mb-1">SCORE</div>
                <div className={`text-2xl font-bold ${reviewData.score >= 8 ? 'text-secondary-accent' : reviewData.score >= 5 ? 'text-accent' : 'text-destructive'}`}>
                  {reviewData.score ?? '?'}/10
                </div>
              </div>
              <div className="border border-accent/20 p-3 bg-surface/60 flex flex-col justify-center items-center text-center">
                <div className="text-[10px] text-muted-foreground mb-1">STATUS</div>
                {reviewData.passed ? (
                  <span className="text-secondary-accent font-bold tracking-widest uppercase text-xs flex items-center gap-1 glow-text"><CheckCircle2 className="w-4 h-4"/> PASSED</span>
                ) : (
                  <span className="text-destructive font-bold tracking-widest uppercase text-xs flex items-center gap-1 glow-text"><XCircle className="w-4 h-4"/> FAILED</span>
                )}
              </div>
            </div>

            {reviewData.violations && reviewData.violations.length > 0 && (
              <div className="border border-destructive/30 bg-destructive/5 p-3">
                <div className="text-[10px] font-bold text-destructive mb-3 uppercase flex items-center border-b border-destructive/20 pb-1">
                  <AlertTriangle className="w-3 h-3 mr-2" /> GLOSSARY_VIOLATIONS ({reviewData.violations.length})
                </div>
                <ul className="space-y-2">
                  {reviewData.violations.map((v, i) => (
                    <li key={i} className="text-[10px] flex items-start gap-2 bg-black/40 p-2 border border-destructive/10">
                      <span className="text-destructive font-bold mt-0.5">[{String(i+1).padStart(2, '0')}]</span>
                      <div>
                        <div className="text-text font-bold mb-0.5">&quot;{v.term}&quot; → <span className="text-destructive line-through opacity-70">{v.found}</span> <span className="text-secondary-accent">{v.expected}</span></div>
                        {v.context && <div className="text-muted-foreground opacity-80">{v.context}</div>}
                      </div>
                    </li>
                  ))}
                </ul>
                
                {correcting ? (
                  <button disabled className="mt-3 w-full p-2 bg-destructive/10 border border-destructive/30 text-destructive text-[10px] uppercase font-bold tracking-widest flex items-center justify-center opacity-50 cursor-not-allowed">
                    <RefreshCw className="w-3 h-3 mr-2 animate-spin" /> EXECUTING_CORRECTIONS...
                  </button>
                ) : (
                  <button onClick={runCorrection} className="mt-3 w-full p-2 bg-destructive/20 border border-destructive/40 text-destructive hover:bg-destructive hover:text-white text-[10px] uppercase font-bold tracking-widest flex items-center justify-center transition-colors">
                    <RefreshCw className="w-3 h-3 mr-2" /> FORCE_AI_CORRECTION
                  </button>
                )}
              </div>
            )}

            {reviewData.style_notes && reviewData.style_notes.length > 0 && (
              <div className="border border-accent/20 bg-accent/5 p-3">
                <div className="text-[10px] font-bold text-accent mb-2 uppercase border-b border-accent/10 pb-1">STYLE_NOTES</div>
                <ul className="list-disc pl-4 space-y-1">
                  {reviewData.style_notes.map((note, i) => (
                    <li key={i} className="text-[10px] text-muted-foreground">{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
