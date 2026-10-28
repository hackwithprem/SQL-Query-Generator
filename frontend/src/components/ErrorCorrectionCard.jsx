import React, { useState } from 'react';
import { AlertCircle, Wrench, Sparkles, Check, ArrowRight } from 'lucide-react';
import { apiClient } from '../api/client';

export default function ErrorCorrectionCard({
  error,
  failedSql,
  question,
  onApplyCorrection
}) {
  const [isFixing, setIsFixing] = useState(false);
  const [correctionResult, setCorrectionResult] = useState(null);
  const [fixError, setFixError] = useState(null);

  if (!error) return null;

  const handleFixWithAI = async () => {
    setIsFixing(true);
    setFixError(null);
    try {
      const res = await apiClient.correctSql(
        question || 'Run query',
        failedSql,
        error
      );
      setCorrectionResult(res);
    } catch (err) {
      setFixError(err.response?.data?.detail || err.message || 'Failed to auto-fix query');
    } finally {
      setIsFixing(false);
    }
  };

  return (
    <div className="rounded-2xl border p-5 space-y-4 border-rose-500/30 bg-rose-950/20 light:bg-rose-50/70 light:border-rose-200 shadow-xl transition-all">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400 shrink-0 mt-0.5">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-rose-200 light:text-rose-900">
              Query Execution Error
            </h4>
            <p className="text-xs font-mono text-rose-300 light:text-rose-700 bg-rose-950/40 p-2.5 rounded-lg border border-rose-800/40 light:bg-rose-100 light:border-rose-300 overflow-x-auto">
              {error}
            </p>
          </div>
        </div>

        {/* AI Correction Trigger */}
        {!correctionResult && (
          <button
            type="button"
            onClick={handleFixWithAI}
            disabled={isFixing}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-amber-500 to-rose-600 hover:from-amber-400 hover:to-rose-500 shadow-md shadow-rose-600/20 active:scale-95 transition-all shrink-0 disabled:opacity-50"
          >
            {isFixing ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Fixing with AI...</span>
              </>
            ) : (
              <>
                <Wrench className="w-3.5 h-3.5" />
                <span>Auto-Fix Query with AI</span>
              </>
            )}
          </button>
        )}
      </div>

      {fixError && (
        <p className="text-xs text-rose-400">Failed to auto-fix: {fixError}</p>
      )}

      {/* Suggested Fix Result */}
      {correctionResult && (
        <div className="pt-3 border-t border-rose-800/40 light:border-rose-200 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-medium text-amber-300 light:text-amber-800">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>AI Suggested Correction:</span>
          </div>

          <p className="text-xs text-slate-300 light:text-slate-700">
            {correctionResult.explanation_of_fix}
          </p>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-sky-300 overflow-x-auto light:bg-slate-900">
            {correctionResult.corrected_sql}
          </div>

          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => onApplyCorrection(correctionResult.corrected_sql)}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 shadow-md shadow-sky-600/20 active:scale-95 transition-all"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Apply Fix to SQL Editor</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
