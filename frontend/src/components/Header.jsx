import React from 'react';
import { ShieldCheck, HardDrive, User as UserIcon, Sparkles } from 'lucide-react';

export default function Header({ 
  targetDesc, 
  onResetToSampleDb, 
  isCustomTarget,
  currentUser,
  onOpenAuth,
  onOpenProfile
}) {
  return (
    <header className="h-14 border-b px-6 flex items-center justify-between border-slate-800 bg-slate-900/60 backdrop-blur-md light:border-slate-200 light:bg-white/80 shrink-0 select-none">
      <div className="flex items-center space-x-3">
        <h2 className="text-sm font-semibold text-slate-100 light:text-slate-800 flex items-center space-x-2">
          <span>SQL Query Workspace</span>
        </h2>
        
        {/* Active Database Target Badge with Reset action */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium border bg-slate-800/80 border-slate-700/60 text-slate-300 light:bg-slate-100 light:border-slate-300 light:text-slate-800">
          {isCustomTarget ? (
            <span className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="truncate max-w-[200px]">{targetDesc}</span>
              <button
                type="button"
                onClick={onResetToSampleDb}
                className="ml-1 text-[10px] text-sky-400 hover:text-sky-300 hover:underline"
                title="Switch back to University Sample DB"
              >
                (Reset to Sample DB)
              </button>
            </span>
          ) : (
            <span className="flex items-center space-x-1.5">
              <HardDrive className="w-3.5 h-3.5 text-indigo-400" />
              <span>Sample Database</span>
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-3 text-xs">
        {/* Read-Only Safety Badge */}
        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="font-medium text-[11px]">Read-Only Guardrails Active</span>
        </div>

        {/* User Profile / Sign In Quick Pill */}
        <button
          type="button"
          onClick={currentUser ? onOpenProfile : onOpenAuth}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 light:bg-slate-100 light:border-slate-300 text-slate-300 light:text-slate-700 hover:border-sky-500 transition-colors"
        >
          <div className="w-5 h-5 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold text-[10px]">
            {currentUser?.full_name ? currentUser.full_name[0].toUpperCase() : <UserIcon className="w-3 h-3" />}
          </div>
          <span className="text-[11px] font-medium">
            {currentUser ? currentUser.full_name : "Sign In"}
          </span>
        </button>
      </div>
    </header>
  );
}
