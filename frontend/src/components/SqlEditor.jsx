import React, { useState } from 'react';
import { 
  Play, 
  HelpCircle, 
  Copy, 
  Check, 
  Trash2, 
  RotateCw, 
  ShieldCheck, 
  AlertTriangle,
  Code2
} from 'lucide-react';

export default function SqlEditor({
  sql,
  setSql,
  onExecute,
  isExecuting,
  onExplain,
  isExplaining,
  onRegenerate,
  isGenerating,
  clarification,
  isSafe
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!sql) return;
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy SQL:", err);
    }
  };

  const lines = (sql || '').split('\n');

  return (
    <div className="rounded-2xl border flex flex-col border-slate-800 bg-slate-900/90 shadow-xl overflow-hidden light:bg-white light:border-slate-200">
      {/* Editor Header Bar */}
      <div className="px-4 py-2.5 border-b flex flex-wrap items-center justify-between gap-2 border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50/80">
        <div className="flex items-center space-x-2.5">
          <Code2 className="w-4 h-4 text-sky-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 light:text-slate-700">
            SQL Editor
          </span>
          {isSafe !== false ? (
            <span className="inline-flex items-center space-x-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="w-3 h-3" />
              <span>Read-Only SELECT</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <AlertTriangle className="w-3 h-3" />
              <span>Safety Review Needed</span>
            </span>
          )}
        </div>

        {/* Toolbar Buttons */}
        <div className="flex items-center space-x-1.5">
          {/* Copy Button */}
          <button
            type="button"
            onClick={handleCopy}
            disabled={!sql}
            className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700/60 light:text-slate-600 light:border-slate-200 light:hover:bg-slate-100 transition-colors disabled:opacity-40"
            title="Copy SQL to Clipboard"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Regenerate Button */}
          <button
            type="button"
            onClick={onRegenerate}
            disabled={isGenerating}
            className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700/60 light:text-slate-600 light:border-slate-200 light:hover:bg-slate-100 transition-colors disabled:opacity-40"
            title="Re-generate SQL"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
            <span>Re-Generate</span>
          </button>

          {/* Clear Editor */}
          <button
            type="button"
            onClick={() => setSql('')}
            disabled={!sql}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800/60 light:hover:bg-slate-100 transition-colors disabled:opacity-30"
            title="Clear Editor"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Clarification Alert if model flagged something */}
      {clarification && (
        <div className="px-4 py-2 border-b bg-amber-500/10 border-amber-500/30 text-amber-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{clarification}</span>
        </div>
      )}

      {/* Editor Body with Line Numbers */}
      <div className="relative flex font-mono text-xs overflow-x-auto min-h-[140px] max-h-[280px]">
        {/* Line Numbers */}
        <div className="select-none py-3 px-3 text-right text-slate-600 bg-slate-950/60 border-r border-slate-800/80 light:bg-slate-100 light:border-slate-200 light:text-slate-400 font-mono text-[11px] leading-6 min-w-[36px]">
          {lines.map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>

        {/* Textarea */}
        <textarea
          id="sql-code-editor"
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          placeholder="-- Generated SQL query will appear here. You can freely edit before executing..."
          spellCheck={false}
          className="w-full py-3 px-4 bg-transparent outline-none resize-none font-mono text-xs leading-6 text-sky-200 placeholder:text-slate-600 light:text-slate-900 light:placeholder:text-slate-400"
        />
      </div>

      {/* Bottom Action Footer */}
      <div className="px-4 py-3 border-t flex items-center justify-between border-slate-800 bg-slate-950/40 light:border-slate-200 light:bg-slate-50">
        <div className="text-[11px] text-slate-500 light:text-slate-400">
          Editable query &bull; Generation and execution are always decoupled.
        </div>

        <div className="flex items-center space-x-2.5">
          {/* Explain Button */}
          <button
            id="explain-sql-button"
            type="button"
            disabled={isExplaining || !sql.trim()}
            onClick={onExplain}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700/80 hover:text-white border border-slate-700 light:bg-white light:border-slate-300 light:text-slate-700 light:hover:bg-slate-100 transition-colors disabled:opacity-40"
          >
            {isExplaining ? (
              <div className="w-3 h-3 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
            ) : (
              <HelpCircle className="w-3.5 h-3.5 text-indigo-400" />
            )}
            <span>Explain Query</span>
          </button>

          {/* Execute Button */}
          <button
            id="execute-query-button"
            type="button"
            disabled={isExecuting || !sql.trim()}
            onClick={onExecute}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 shadow-md shadow-emerald-600/20 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isExecuting ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Executing...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Execute Query</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
