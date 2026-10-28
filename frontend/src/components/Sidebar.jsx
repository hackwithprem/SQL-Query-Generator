import React from 'react';
import { 
  Database, 
  History, 
  Settings, 
  HelpCircle, 
  PlusCircle, 
  Sun, 
  Moon, 
  Table2, 
  CheckCircle2, 
  AlertCircle,
  Sparkles,
  Terminal
} from 'lucide-react';

export default function Sidebar({ 
  onNewQuery, 
  onOpenSchema, 
  onOpenHistory, 
  onOpenSettings, 
  onOpenSamples,
  theme, 
  onToggleTheme,
  health
}) {
  const isHealthy = health?.status === 'healthy';
  const providerName = health?.ai_provider?.provider || 'AI Provider';

  return (
    <aside className="w-64 border-r flex flex-col justify-between shrink-0 transition-colors duration-200 border-slate-800 bg-slate-900/95 light:border-slate-200 light:bg-white">
      {/* Brand & New Query */}
      <div className="p-4 space-y-4">
        <div className="flex items-center space-x-3 px-1 py-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white font-bold">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-sm leading-tight text-slate-100 light:text-slate-900">
              SQL GenAI
            </h1>
            <p className="text-[11px] text-slate-400 light:text-slate-500">
              Plain English to SQL
            </p>
          </div>
        </div>

        {/* New Query Primary Action */}
        <button
          onClick={onNewQuery}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl text-sm font-medium transition-all duration-150 shadow-sm bg-sky-600 hover:bg-sky-500 text-white active:scale-[0.98]"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Query</span>
        </button>

        {/* Navigation Actions */}
        <nav className="space-y-1 pt-2">
          <button
            onClick={onOpenSchema}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 light:text-slate-600 light:hover:text-slate-900 light:hover:bg-slate-100"
          >
            <Table2 className="w-4 h-4 text-sky-400" />
            <span>Database Schema</span>
          </button>

          <button
            onClick={onOpenHistory}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 light:text-slate-600 light:hover:text-slate-900 light:hover:bg-slate-100"
          >
            <History className="w-4 h-4 text-indigo-400" />
            <span>Query History</span>
          </button>

          <button
            onClick={onOpenSamples}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 light:text-slate-600 light:hover:text-slate-900 light:hover:bg-slate-100"
          >
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Sample Questions</span>
          </button>

          <button
            onClick={onOpenSettings}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 light:text-slate-600 light:hover:text-slate-900 light:hover:bg-slate-100"
          >
            <Settings className="w-4 h-4 text-slate-400" />
            <span>System Settings</span>
          </button>
        </nav>
      </div>

      {/* System Status & Theme Toggle Footer */}
      <div className="p-4 border-t space-y-3 border-slate-800/80 light:border-slate-200">
        {/* Status Pill */}
        <div className="p-2.5 rounded-lg border text-xs space-y-1.5 bg-slate-800/50 border-slate-700/60 light:bg-slate-50 light:border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 light:text-slate-500 font-medium">Database</span>
            <div className="flex items-center space-x-1.5">
              <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              <span className="font-semibold text-[11px] text-slate-200 light:text-slate-700">
                {isHealthy ? 'Connected (SQLite)' : 'Disconnected'}
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 light:text-slate-500">
            <span>Engine</span>
            <span className="truncate max-w-[110px] text-sky-400 font-mono text-[10px]">
              {providerName}
            </span>
          </div>
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={onToggleTheme}
          className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800/60 light:text-slate-700 light:hover:bg-slate-100 transition-colors"
        >
          <span className="flex items-center space-x-2">
            {theme === 'dark' ? <Moon className="w-4 h-4 text-indigo-400" /> : <Sun className="w-4 h-4 text-amber-500" />}
            <span>{theme === 'dark' ? 'Dark Mode' : 'Light Mode'}</span>
          </span>
          <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-slate-800 light:bg-slate-200 text-slate-400 light:text-slate-600">
            {theme}
          </span>
        </button>
      </div>
    </aside>
  );
}
