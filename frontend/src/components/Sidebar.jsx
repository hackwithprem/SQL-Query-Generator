import React from 'react';
import {
  Database,
  History,
  PlusCircle,
  Sun,
  Moon,
  UploadCloud,
  User,
  LogOut,
  LogIn,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';

export default function Sidebar({
  onNewQuery,
  onOpenHistory,
  onOpenUploadData,
  onOpenProfile,
  onOpenAuth,
  onSignOut,
  currentUser,
  theme,
  onToggleTheme,
  isOpen,
  onToggle,
}) {
  return (
    <>
      {/* ═══════════════════════════════════════════════════════════════════
          DESKTOP SIDEBAR  (hidden on mobile, md and above)
          Collapsed  → w-[66px]: logo icon + reopen button only
          Expanded   → w-64:     full sidebar
      ════════════════════════════════════════════════════════════════════ */}
      <aside
        className={[
          'hidden md:flex flex-col shrink-0 overflow-hidden',
          'border-r border-slate-800 bg-slate-900/95',
          'light:border-slate-200 light:bg-white select-none',
          'transition-[width] duration-300 ease-in-out',
          isOpen ? 'w-64' : 'w-[66px]',
        ].join(' ')}
      >
        {/* ── Brand strip — always visible ────────────────────────────── */}
        {isOpen ? (
          /* EXPANDED: logo + text + close button in a single row */
          <div className="flex items-center justify-between gap-2 px-3 h-14 border-b border-slate-800/60 light:border-slate-200 shrink-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 shrink-0">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="font-semibold text-sm leading-tight text-slate-100 light:text-slate-900 truncate">
                SQL GenAI
              </h1>
              <p className="text-[11px] text-slate-400 light:text-slate-500 truncate">
                Plain English to SQL
              </p>
            </div>
            <button
              type="button"
              onClick={onToggle}
              aria-label="Hide sidebar"
              title="Hide sidebar"
              className="shrink-0 p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 light:text-slate-500 light:hover:text-slate-900 light:hover:bg-slate-100 transition-colors"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          </div>
        ) : (
          /* COLLAPSED: logo icon on top, open button below — no nav, no footer */
          <div className="flex flex-col items-center pt-3 pb-2 gap-3 shrink-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Database className="w-5 h-5 text-white" />
            </div>
            <button
              type="button"
              onClick={onToggle}
              aria-label="Show sidebar"
              title="Show sidebar"
              className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 light:text-slate-500 light:hover:text-slate-900 light:hover:bg-slate-100 transition-colors"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ── Navigation — completely hidden when collapsed ─────────────
            Using conditional rendering (not overflow clipping) so no
            icons bleed through in the collapsed state.
        ─────────────────────────────────────────────────────────────── */}
        {isOpen && (
          <nav className="flex-1 p-3 space-y-1.5 overflow-y-auto">
            {/* 1. New Query */}
            <button
              id="sidebar-new-query"
              type="button"
              onClick={onNewQuery}
              className="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 bg-sky-600 hover:bg-sky-500 text-white shadow-sm active:scale-[0.98]"
            >
              <PlusCircle className="w-4 h-4 shrink-0" />
              <span>New Query</span>
            </button>

            {/* 2. Query History */}
            <button
              id="sidebar-query-history"
              type="button"
              onClick={currentUser ? onOpenHistory : onOpenAuth}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 light:text-slate-600 light:hover:text-slate-900 light:hover:bg-slate-100"
            >
              <History className="w-4 h-4 text-sky-400 shrink-0" />
              <span>Query History</span>
            </button>

            {/* 3. Upload Data */}
            <button
              id="sidebar-upload-data"
              type="button"
              onClick={currentUser ? onOpenUploadData : onOpenAuth}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 light:text-slate-600 light:hover:text-slate-900 light:hover:bg-slate-100"
            >
              <UploadCloud className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Upload Data</span>
            </button>

            {/* 4. Profile */}
            <button
              id="sidebar-profile"
              type="button"
              onClick={currentUser ? onOpenProfile : onOpenAuth}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 light:text-slate-600 light:hover:text-slate-900 light:hover:bg-slate-100"
            >
              <User className="w-4 h-4 text-indigo-400 shrink-0" />
              <span>Profile</span>
            </button>

            {/* 5. Logout / Sign In */}
            {currentUser ? (
              <button
                id="sidebar-logout"
                type="button"
                onClick={onSignOut}
                className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 light:text-rose-600 light:hover:bg-rose-50"
              >
                <LogOut className="w-4 h-4 shrink-0" />
                <span>Logout</span>
              </button>
            ) : (
              <button
                id="sidebar-signin"
                type="button"
                onClick={onOpenAuth}
                className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-sky-400 hover:text-sky-300 hover:bg-sky-500/10 light:text-sky-600 light:hover:bg-sky-50"
              >
                <LogIn className="w-4 h-4 shrink-0" />
                <span>Sign In</span>
              </button>
            )}

            {/* 6. Light / Dark Mode */}
            <button
              id="sidebar-theme-toggle"
              type="button"
              onClick={onToggleTheme}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80 light:text-slate-600 light:hover:text-slate-900 light:hover:bg-slate-100"
            >
              <div className="flex items-center space-x-3">
                {theme === 'dark'
                  ? <Moon className="w-4 h-4 text-amber-400 shrink-0" />
                  : <Sun  className="w-4 h-4 text-amber-500 shrink-0" />}
                <span>{theme === 'dark' ? 'Dark Mode' : 'Light Mode'}</span>
              </div>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 light:bg-slate-200 light:text-slate-600">
                {theme === 'dark' ? 'Dark' : 'Light'}
              </span>
            </button>
          </nav>
        )}

        {/* ── User footer — completely hidden when collapsed ─────────── */}
        {isOpen && (
          <div className="p-3 border-t border-slate-800/80 light:border-slate-200 shrink-0">
            {currentUser ? (
              <div
                onClick={onOpenProfile}
                className="flex items-center space-x-3 p-2 rounded-xl bg-slate-800/40 hover:bg-slate-800/70 border border-slate-700/50 light:bg-slate-50 light:border-slate-200 light:hover:bg-slate-100 cursor-pointer transition-colors"
              >
                <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 font-bold text-xs flex items-center justify-center shrink-0">
                  {currentUser.full_name ? currentUser.full_name[0].toUpperCase() : 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-slate-200 light:text-slate-800 truncate">
                    {currentUser.full_name || 'User'}
                  </p>
                  <p className="text-[10px] text-slate-400 light:text-slate-500 truncate">
                    {currentUser.email}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center p-2 rounded-xl bg-slate-800/30 border border-slate-700/40 light:bg-slate-50 light:border-slate-200">
                <p className="text-[11px] text-slate-400 light:text-slate-500">
                  Public Guest Session
                </p>
                <button
                  type="button"
                  onClick={onOpenAuth}
                  className="mt-1 text-xs text-sky-400 font-medium hover:underline"
                >
                  Sign in to save queries
                </button>
              </div>
            )}
          </div>
        )}
      </aside>

      {/* ═══════════════════════════════════════════════════════════════════
          MOBILE DRAWER  (visible only below md breakpoint)
          Off-canvas slide-in with backdrop — unchanged
      ════════════════════════════════════════════════════════════════════ */}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={onToggle}
          aria-hidden="true"
        />
      )}

      {/* Drawer panel */}
      <aside
        className={[
          'md:hidden fixed inset-y-0 left-0 z-50 w-64 flex flex-col',
          'border-r border-slate-800 bg-slate-900 select-none',
          'transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
      >
        {/* Brand row */}
        <div className="flex items-center h-14 px-3 gap-2 border-b border-slate-800/60 shrink-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 shrink-0">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="font-semibold text-sm leading-tight text-slate-100">SQL GenAI</h1>
            <p className="text-[11px] text-slate-400">Plain English to SQL</p>
          </div>
          <button
            type="button"
            onClick={onToggle}
            aria-label="Close sidebar"
            title="Close sidebar"
            className="shrink-0 p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1.5 overflow-y-auto">
          <button
            type="button"
            onClick={() => { onNewQuery(); onToggle(); }}
            className="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 bg-sky-600 hover:bg-sky-500 text-white shadow-sm active:scale-[0.98]"
          >
            <PlusCircle className="w-4 h-4 shrink-0" />
            <span>New Query</span>
          </button>

          <button
            type="button"
            onClick={() => { (currentUser ? onOpenHistory : onOpenAuth)(); onToggle(); }}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80"
          >
            <History className="w-4 h-4 text-sky-400 shrink-0" />
            <span>Query History</span>
          </button>

          <button
            type="button"
            onClick={() => { (currentUser ? onOpenUploadData : onOpenAuth)(); onToggle(); }}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80"
          >
            <UploadCloud className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Upload Data</span>
          </button>

          <button
            type="button"
            onClick={() => { (currentUser ? onOpenProfile : onOpenAuth)(); onToggle(); }}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80"
          >
            <User className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>Profile</span>
          </button>

          {currentUser ? (
            <button
              type="button"
              onClick={() => { onSignOut(); onToggle(); }}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
            >
              <LogOut className="w-4 h-4 shrink-0" />
              <span>Logout</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => { onOpenAuth(); onToggle(); }}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-sky-400 hover:text-sky-300 hover:bg-sky-500/10"
            >
              <LogIn className="w-4 h-4 shrink-0" />
              <span>Sign In</span>
            </button>
          )}

          <button
            type="button"
            onClick={onToggleTheme}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/80"
          >
            <div className="flex items-center space-x-3">
              {theme === 'dark'
                ? <Moon className="w-4 h-4 text-amber-400 shrink-0" />
                : <Sun  className="w-4 h-4 text-amber-500 shrink-0" />}
              <span>{theme === 'dark' ? 'Dark Mode' : 'Light Mode'}</span>
            </div>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
              {theme === 'dark' ? 'Dark' : 'Light'}
            </span>
          </button>
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-slate-800/80 shrink-0">
          {currentUser ? (
            <div
              onClick={() => { onOpenProfile(); onToggle(); }}
              className="flex items-center space-x-3 p-2 rounded-xl bg-slate-800/40 hover:bg-slate-800/70 border border-slate-700/50 cursor-pointer transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 font-bold text-xs flex items-center justify-center shrink-0">
                {currentUser.full_name ? currentUser.full_name[0].toUpperCase() : 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-200 truncate">
                  {currentUser.full_name || 'User'}
                </p>
                <p className="text-[10px] text-slate-400 truncate">{currentUser.email}</p>
              </div>
            </div>
          ) : (
            <div className="text-center p-2 rounded-xl bg-slate-800/30 border border-slate-700/40">
              <p className="text-[11px] text-slate-400">Public Guest Session</p>
              <button
                type="button"
                onClick={() => { onOpenAuth(); onToggle(); }}
                className="mt-1 text-xs text-sky-400 font-medium hover:underline"
              >
                Sign in to save queries
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile hamburger — shown only when drawer is closed */}
      {!isOpen && (
        <button
          type="button"
          onClick={onToggle}
          aria-label="Show sidebar"
          title="Show sidebar"
          className="md:hidden fixed top-3 left-3 z-40 p-2 rounded-md bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors shadow-md"
        >
          <PanelLeftOpen className="w-4 h-4" />
        </button>
      )}
    </>
  );
}
