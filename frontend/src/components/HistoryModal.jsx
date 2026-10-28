import React from 'react';
import { 
  X, 
  History, 
  Trash2, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  CornerDownRight 
} from 'lucide-react';

export default function HistoryModal({
  isOpen,
  onClose,
  history,
  onLoadQuery,
  onClearHistory
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-3xl h-[80vh] rounded-2xl border flex flex-col overflow-hidden shadow-2xl border-slate-800 bg-slate-900 text-slate-100 light:bg-white light:border-slate-200 light:text-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">Query History</h3>
              <p className="text-xs text-slate-400 light:text-slate-500">
                Recent natural language questions and generated SQL
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {history.length > 0 && (
              <button
                onClick={onClearHistory}
                className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium text-rose-400 hover:bg-rose-500/10 border border-rose-500/20 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear History</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 light:hover:text-slate-800 light:hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {history.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center space-y-2 text-center text-slate-500">
              <History className="w-10 h-10 stroke-[1.5]" />
              <p className="text-xs">No recent queries in history.</p>
            </div>
          ) : (
            history.map((item) => {
              const isSuccess = item.status === 'executed';
              const isFailed = item.status === 'failed' || item.status === 'validation_error';

              return (
                <div
                  key={item.id}
                  className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/40 hover:border-slate-700 transition-all space-y-2.5 light:bg-slate-50 light:border-slate-200"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        {isSuccess && (
                          <span className="flex items-center space-x-1 text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Executed ({item.row_count} rows)</span>
                          </span>
                        )}
                        {isFailed && (
                          <span className="flex items-center space-x-1 text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/30">
                            <AlertCircle className="w-3 h-3" />
                            <span>Failed</span>
                          </span>
                        )}
                        {!isSuccess && !isFailed && (
                          <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-sky-500/15 text-sky-400 border border-sky-500/30">
                            Generated
                          </span>
                        )}

                        <span className="text-[11px] text-slate-500 font-mono">
                          {item.created_at || 'Just now'}
                        </span>

                        {item.execution_time_ms && (
                          <span className="text-[11px] text-slate-500 font-mono">
                            &bull; {item.execution_time_ms} ms
                          </span>
                        )}
                      </div>

                      <p className="text-xs font-medium text-slate-200 light:text-slate-800 pt-0.5">
                        "{item.natural_query}"
                      </p>
                    </div>

                    <button
                      onClick={() => {
                        onLoadQuery(item.generated_sql, item.natural_query);
                        onClose();
                      }}
                      className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-sky-400 bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/20 shrink-0 transition-colors"
                      title="Load query into SQL Editor"
                    >
                      <span>Load Query</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* SQL Preview */}
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 font-mono text-[11px] text-sky-200 overflow-x-auto light:bg-slate-900 light:text-sky-300">
                    {item.generated_sql}
                  </div>

                  {item.error_message && (
                    <p className="text-[11px] text-rose-400 font-mono">
                      Error: {item.error_message}
                    </p>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
