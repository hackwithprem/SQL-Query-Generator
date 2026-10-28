import React from 'react';
import { 
  X, 
  Settings, 
  Cpu, 
  ShieldCheck, 
  Database, 
  KeyRound, 
  Info 
} from 'lucide-react';

export default function SettingsModal({
  isOpen,
  onClose,
  health
}) {
  if (!isOpen) return null;

  const provider = health?.ai_provider?.provider || 'Unknown';
  const configured = health?.ai_provider?.configured_provider || 'groq';
  const isHealthy = health?.status === 'healthy';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-2xl rounded-2xl border flex flex-col overflow-hidden shadow-2xl border-slate-800 bg-slate-900 text-slate-100 light:bg-white light:border-slate-200 light:text-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-slate-800 text-slate-300 light:bg-slate-200 light:text-slate-700">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">System Configuration & Settings</h3>
              <p className="text-xs text-slate-400 light:text-slate-500">
                AI provider, database connectivity, and security guardrails
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 light:hover:text-slate-800 light:hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[70vh]">
          {/* AI Provider Section */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-sky-400" />
              Generative AI Provider
            </h4>
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-3 light:bg-slate-50 light:border-slate-200">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Active Engine:</span>
                <span className="font-mono text-sky-400 font-semibold">{provider}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Configured Provider:</span>
                <span className="font-mono uppercase text-slate-200 light:text-slate-800">{configured}</span>
              </div>
              <div className="pt-2 border-t border-slate-800/80 light:border-slate-200 text-xs text-slate-400 leading-relaxed">
                To connect your live Groq API key or Gemini API key, edit the <code className="px-1.5 py-0.5 rounded bg-slate-800 font-mono text-[11px] text-sky-300 light:bg-slate-200">backend/.env</code> file with:
                <div className="mt-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-emerald-400 light:bg-slate-900">
                  GROQ_API_KEY=gsk_your_groq_api_key<br />
                  GROQ_MODEL=llama-3.3-70b-versatile
                </div>
              </div>
            </div>
          </div>

          {/* Database Section */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              Database Engine
            </h4>
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-2 light:bg-slate-50 light:border-slate-200 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Database Status:</span>
                <span className={`font-semibold ${isHealthy ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {isHealthy ? 'Connected & Operational' : 'Offline'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Engine Type:</span>
                <span className="font-mono text-slate-200 light:text-slate-800">SQLite 3 (sample.db)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Tables Loaded:</span>
                <span className="font-mono text-slate-200 light:text-slate-800">students, courses, enrollments, marks, departments</span>
              </div>
            </div>
          </div>

          {/* Security Guardrails Section */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Security & Safety Guardrails
            </h4>
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-2 text-xs text-slate-400 light:bg-slate-50 light:border-slate-200">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <ShieldCheck className="w-4 h-4" />
                <span>Strict Read-Only SELECT Enforcement</span>
              </div>
              <p className="leading-relaxed">
                All queries undergo dialect-aware token inspection before execution.
                Any non-SELECT statements (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE) or multiple statements separated by semicolons are immediately rejected.
              </p>
              <div className="pt-2 flex items-center justify-between text-[11px] text-slate-500">
                <span>Row Limit: 500 rows</span>
                <span>Execution Timeout: 10s</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
