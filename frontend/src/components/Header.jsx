import React from 'react';
import { ShieldCheck, Cpu, HardDrive } from 'lucide-react';

export default function Header({ health }) {
  const isHealthy = health?.status === 'healthy';
  const provider = health?.ai_provider?.provider || 'AI Engine';

  return (
    <header className="h-14 border-b px-6 flex items-center justify-between border-slate-800 bg-slate-900/60 backdrop-blur-md light:border-slate-200 light:bg-white/80 shrink-0">
      <div className="flex items-center space-x-3">
        <h2 className="text-sm font-semibold text-slate-100 light:text-slate-800">
          SQL Query Workspace
        </h2>
        <span className="text-xs px-2 py-0.5 rounded-full font-mono font-medium text-slate-400 bg-slate-800/80 light:bg-slate-100 light:text-slate-600 border border-slate-700/60 light:border-slate-300">
          v1.0.0
        </span>
      </div>

      <div className="flex items-center space-x-3 text-xs">
        {/* Read-Only Safety Badge */}
        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="font-medium text-[11px]">Read-Only Protected</span>
        </div>

        {/* AI Provider Badge */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400">
          <Cpu className="w-3.5 h-3.5" />
          <span className="font-mono text-[11px] font-medium">{provider}</span>
        </div>

        {/* Database Status */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 light:bg-slate-100 light:border-slate-200 text-slate-300 light:text-slate-700">
          <HardDrive className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-[11px] font-medium">SQLite Sample DB</span>
        </div>
      </div>
    </header>
  );
}
