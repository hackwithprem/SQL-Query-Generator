import React from 'react';
import { HelpCircle, X, Sparkles, BookOpen } from 'lucide-react';

export default function ExplanationCard({ explanation, onClose }) {
  if (!explanation) return null;

  return (
    <div className="rounded-2xl border p-5 space-y-3 border-indigo-500/30 bg-indigo-950/20 backdrop-blur-sm light:bg-indigo-50/60 light:border-indigo-200 shadow-xl transition-all animate-in fade-in slide-in-from-top-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400">
            <BookOpen className="w-4 h-4" />
          </div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-indigo-300 light:text-indigo-900">
            Query Explanation in Plain English
          </h4>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 light:hover:text-slate-700 transition-colors p-1"
          title="Close explanation"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="text-xs leading-relaxed text-slate-300 light:text-slate-700 whitespace-pre-line space-y-2 font-normal">
        {explanation}
      </div>
    </div>
  );
}
